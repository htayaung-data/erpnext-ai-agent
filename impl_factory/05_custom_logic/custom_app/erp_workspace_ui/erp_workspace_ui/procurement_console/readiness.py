from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from . import common, item_buying_profile, service, supplier_readiness


MANAGER_ROLES = {"Purchase Manager", "Purchase Master Manager"}
ISSUE_LIMIT = 24

GROUP_LABELS = {
	"supplier_readiness": "Supplier readiness",
	"item_readiness": "Item buying readiness",
	"purchase_request_readiness": "Purchase request readiness",
	"rfq_readiness": "RFQ readiness",
	"supplier_quotation_readiness": "Supplier quotation readiness",
	"purchase_order_readiness": "Purchase order readiness",
}

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2, "ready": 3}


def _is_manager(context: dict[str, object] | None = None) -> bool:
	roles = set((context or {}).get("roles") or []) if context and "roles" in context else service.current_user_roles()
	return bool(roles.intersection(MANAGER_ROLES))


def _route(route: str, *parts: object) -> dict[str, object]:
	return {
		"kind": "page",
		"route": route,
		"route_parts": [cstr(part).strip() for part in parts if cstr(part).strip()],
	}


def _worklist(queue_key: str, filters: dict[str, object] | None = None) -> dict[str, object]:
	return {"kind": "worklist", "queue_key": queue_key, "filters": filters or {}}


def _issue(
	key: str,
	group: str,
	severity: str,
	title: str,
	detail: str,
	source_type: str,
	source_name: str,
	*,
	fix_label: str = "",
	fix_route: dict[str, object] | None = None,
	deferred_action: str = "",
) -> dict[str, object]:
	return {
		"key": key,
		"group": group,
		"group_label": GROUP_LABELS.get(group, group.replace("_", " ").title()),
		"severity": severity if severity in SEVERITY_ORDER else "info",
		"title": title,
		"detail": detail,
		"source_type": source_type,
		"source_name": source_name,
		"fix_label": fix_label,
		"fix_route": fix_route or {},
		"deferred_action": deferred_action,
		"productized_only": True,
	}


def _ready_issue(group: str, source_type: str, source_name: str, title: str, detail: str) -> dict[str, object]:
	return _issue(
		f"{group}:{source_name}:ready",
		group,
		"ready",
		title,
		detail,
		source_type,
		source_name,
	)


def _sort_issues(issues: list[dict[str, object]]) -> list[dict[str, object]]:
	return sorted(
		issues,
		key=lambda row: (SEVERITY_ORDER.get(cstr(row.get("severity")), 9), cstr(row.get("group")), cstr(row.get("source_name"))),
	)


def _summary(issues: list[dict[str, object]]) -> dict[str, object]:
	counts = {"critical": 0, "warning": 0, "info": 0, "ready": 0}
	for issue in issues:
		severity = cstr(issue.get("severity")).strip() or "info"
		if severity in counts:
			counts[severity] += 1
	return {
		"critical": counts["critical"],
		"warning": counts["warning"],
		"info": counts["info"],
		"ready": counts["ready"],
		"total": len(issues),
	}


def _context_payload(source_type: str, source_name: str, issues: list[dict[str, object]]) -> dict[str, object]:
	ordered = _sort_issues(issues)
	return {
		"state": common.ready_state(),
		"source_type": source_type,
		"source_name": source_name,
		"summary": _summary(ordered),
		"issues": ordered,
		"empty_message": "No readiness issues found for current checks.",
		"productized_only": True,
	}


def _safe_get_doc(doctype: str, name: str):
	doc_name = cstr(name).strip()
	if not doc_name or not common.can_read(doctype):
		return None
	try:
		doc = frappe.get_doc(doctype, doc_name)
		if hasattr(doc, "check_permission"):
			doc.check_permission("read")
		return doc
	except Exception:
		return None


def _child_rows(doc: object, fieldname: str) -> list[object]:
	rows = getattr(doc, fieldname, None)
	if rows is None and isinstance(doc, dict):
		rows = doc.get(fieldname)
	return list(rows or [])


def _value(row: object, fieldname: str, default: Any = "") -> Any:
	if isinstance(row, dict):
		return row.get(fieldname, default)
	return getattr(row, fieldname, default)


def _missing(value: object) -> bool:
	return cstr(value).strip() == ""


def _qty_missing(value: object) -> bool:
	return flt(value) <= 0


def _supplier_label(supplier: str) -> str:
	name = cstr(supplier).strip()
	if not name:
		return "Supplier"
	try:
		row = frappe.db.get_value("Supplier", name, ["supplier_name"], as_dict=True) or {}
		return cstr(row.get("supplier_name") or name).strip()
	except Exception:
		return name


def get_supplier_readiness_context(supplier: str) -> dict[str, object]:
	supplier_name = cstr(supplier).strip()
	if not supplier_name:
		return _context_payload("Supplier", "", [])
	profile = supplier_readiness.get_supplier_profile_for_readiness(supplier_name)
	status = cstr(profile.get("buying_readiness_status") or profile.get("readiness_label")).strip() or supplier_readiness.NO_PROFILE
	issues: list[dict[str, object]] = []
	if not profile.get("exists") or status == supplier_readiness.NO_PROFILE:
		issues.append(_issue(
			f"supplier:{supplier_name}:profile_missing",
			"supplier_readiness",
			"warning",
			"Supplier profile not reviewed",
			"Review the Supplier Buying Profile before relying on this supplier for sourcing decisions.",
			"Supplier",
			supplier_name,
			fix_label="Review supplier profile",
			fix_route=_route("procurement-console-supplier", supplier_name),
		))
	elif status == supplier_readiness.HOLD_FOR_SOURCING:
		issues.append(_issue(
			f"supplier:{supplier_name}:hold",
			"supplier_readiness",
			"critical",
			"Supplier is on hold for sourcing",
			cstr(profile.get("readiness_note")).strip() or "Supplier readiness is blocked by the buying profile.",
			"Supplier",
			supplier_name,
			fix_label="Review supplier profile",
			fix_route=_route("procurement-console-supplier", supplier_name),
		))
	elif status in {supplier_readiness.NEEDS_EMAIL, supplier_readiness.NEEDS_CONTACT_REVIEW}:
		issues.append(_issue(
			f"supplier:{supplier_name}:needs_review",
			"supplier_readiness",
			"warning",
			status,
			cstr(profile.get("readiness_note")).strip() or "Supplier contact readiness needs manager review.",
			"Supplier",
			supplier_name,
			fix_label="Review supplier profile",
			fix_route=_route("procurement-console-supplier", supplier_name),
		))
	else:
		issues.append(_ready_issue("supplier_readiness", "Supplier", supplier_name, "Supplier profile ready", "Supplier Buying Profile has no blocking readiness issue."))
	return _context_payload("Supplier", supplier_name, issues)


def get_item_buying_readiness_context(item_code: str) -> dict[str, object]:
	item_name = cstr(item_code).strip()
	if not item_name:
		return _context_payload("Item", "", [])
	profile = item_buying_profile.get_item_profile_context(item_name)
	status = cstr(profile.get("buying_readiness_status") or profile.get("readiness_label")).strip() or item_buying_profile.NOT_REVIEWED
	issues: list[dict[str, object]] = []
	if not profile.get("exists") or status == item_buying_profile.NOT_REVIEWED:
		issues.append(_issue(
			f"item:{item_name}:not_reviewed",
			"item_readiness",
			"warning",
			"Item buying context not reviewed",
			"Review the Buying Procurement Context before using this item in sourcing or order decisions.",
			"Item",
			item_name,
			fix_label="Review item context",
			fix_route=_route("procurement-console-item", item_name),
		))
	elif status == item_buying_profile.HOLD_FOR_SOURCING:
		issues.append(_issue(
			f"item:{item_name}:hold",
			"item_readiness",
			"critical",
			"Item is on hold for sourcing",
			cstr(profile.get("readiness_note")).strip() or "Item buying readiness blocks sourcing use.",
			"Item",
			item_name,
			fix_label="Review item context",
			fix_route=_route("procurement-console-item", item_name),
		))
	elif status == item_buying_profile.NEEDS_SOURCING_REVIEW:
		issues.append(_issue(
			f"item:{item_name}:needs_review",
			"item_readiness",
			"warning",
			"Item needs sourcing review",
			cstr(profile.get("readiness_note")).strip() or "Item buying context needs manager review.",
			"Item",
			item_name,
			fix_label="Review item context",
			fix_route=_route("procurement-console-item", item_name),
		))
	else:
		issues.append(_ready_issue("item_readiness", "Item", item_name, "Item buying context ready", "Buying Procurement Context has no blocking readiness issue."))
	return _context_payload("Item", item_name, issues)


def _supplier_issues_for_document(suppliers: list[object], parent_key: str, group: str) -> list[dict[str, object]]:
	issues: list[dict[str, object]] = []
	if not suppliers:
		issues.append(_issue(
			f"{parent_key}:supplier_missing",
			group,
			"critical",
			"No suppliers selected",
			"Add supplier context through the governed productized form before a future supplier communication step.",
			parent_key.split(":", 1)[0],
			parent_key.split(":", 1)[-1],
			deferred_action="Future governed sourcing step",
		))
		return issues
	for row in suppliers:
		supplier = cstr(_value(row, "supplier") or _value(row, "supplier_name")).strip()
		if not supplier:
			issues.append(_issue(
				f"{parent_key}:supplier_row_blank",
				group,
				"critical",
				"Supplier row is incomplete",
				"A supplier row is missing supplier identity.",
				parent_key.split(":", 1)[0],
				parent_key.split(":", 1)[-1],
			))
			continue
		profile = supplier_readiness.get_supplier_profile_for_readiness(supplier)
		status = cstr(profile.get("buying_readiness_status") or profile.get("readiness_label")).strip() or supplier_readiness.NO_PROFILE
		if status == supplier_readiness.HOLD_FOR_SOURCING:
			issues.append(_issue(
				f"{parent_key}:supplier:{supplier}:hold",
				group,
				"critical",
				"Supplier on hold",
				f"{_supplier_label(supplier)} is held in Supplier Buying Profile.",
				"Supplier",
				supplier,
				fix_label="Review supplier profile",
				fix_route=_route("procurement-console-supplier", supplier),
			))
		elif status in {supplier_readiness.NO_PROFILE, supplier_readiness.NEEDS_EMAIL, supplier_readiness.NEEDS_CONTACT_REVIEW}:
			issues.append(_issue(
				f"{parent_key}:supplier:{supplier}:review",
				group,
				"warning",
				"Supplier readiness needs review",
				f"{_supplier_label(supplier)} readiness is {status}.",
				"Supplier",
				supplier,
				fix_label="Review supplier profile",
				fix_route=_route("procurement-console-supplier", supplier),
			))
	return issues


def _item_issues_for_document(items: list[object], parent_key: str, group: str) -> list[dict[str, object]]:
	issues: list[dict[str, object]] = []
	if not items:
		issues.append(_issue(
			f"{parent_key}:items_missing",
			group,
			"critical",
			"No item lines",
			"Add item lines through the governed productized form before future downstream action.",
			parent_key.split(":", 1)[0],
			parent_key.split(":", 1)[-1],
			deferred_action="Future governed document step",
		))
		return issues
	for index, row in enumerate(items, start=1):
		item = cstr(_value(row, "item_code")).strip()
		if not item:
			issues.append(_issue(
				f"{parent_key}:item_row:{index}:missing",
				group,
				"critical",
				"Item row is incomplete",
				"An item line is missing item identity.",
				parent_key.split(":", 1)[0],
				parent_key.split(":", 1)[-1],
			))
			continue
		profile = item_buying_profile.get_item_profile_context(item)
		status = cstr(profile.get("buying_readiness_status") or profile.get("readiness_label")).strip() or item_buying_profile.NOT_REVIEWED
		if status == item_buying_profile.HOLD_FOR_SOURCING:
			issues.append(_issue(
				f"{parent_key}:item:{item}:hold",
				group,
				"critical",
				"Item on hold",
				f"{item} is held in Buying Procurement Context.",
				"Item",
				item,
				fix_label="Review item context",
				fix_route=_route("procurement-console-item", item),
			))
		elif status in {item_buying_profile.NOT_REVIEWED, item_buying_profile.NEEDS_SOURCING_REVIEW}:
			issues.append(_issue(
				f"{parent_key}:item:{item}:review",
				group,
				"warning",
				"Item buying context needs review",
				f"{item} readiness is {status}.",
				"Item",
				item,
				fix_label="Review item context",
				fix_route=_route("procurement-console-item", item),
			))
	return issues


def _line_quality_issues(items: list[object], parent_key: str, group: str, *, require_rate: bool = False, require_schedule: bool = False) -> list[dict[str, object]]:
	issues: list[dict[str, object]] = []
	for index, row in enumerate(items, start=1):
		item = cstr(_value(row, "item_code") or f"Line {index}").strip()
		if _qty_missing(_value(row, "qty")):
			issues.append(_issue(f"{parent_key}:line:{index}:qty", group, "critical", "Line quantity missing", f"{item} needs a positive quantity.", parent_key.split(":", 1)[0], parent_key.split(":", 1)[-1]))
		if _missing(_value(row, "uom")):
			issues.append(_issue(f"{parent_key}:line:{index}:uom", group, "warning", "Line UOM missing", f"{item} needs a unit of measure before future document action.", parent_key.split(":", 1)[0], parent_key.split(":", 1)[-1]))
		if require_rate and flt(_value(row, "rate")) <= 0:
			issues.append(_issue(f"{parent_key}:line:{index}:rate", group, "critical", "Line rate missing", f"{item} needs a positive rate before future manager review.", parent_key.split(":", 1)[0], parent_key.split(":", 1)[-1]))
		if require_schedule and _missing(_value(row, "schedule_date") or _value(row, "required_date")):
			issues.append(_issue(f"{parent_key}:line:{index}:date", group, "warning", "Required date missing", f"{item} needs a required date before future downstream action.", parent_key.split(":", 1)[0], parent_key.split(":", 1)[-1]))
	return issues


def get_purchase_request_readiness_context(name: str) -> dict[str, object]:
	doc = _safe_get_doc("Material Request", name)
	if not doc:
		return _context_payload("Material Request", cstr(name).strip(), [])
	items = _child_rows(doc, "items")
	parent_key = f"Material Request:{cstr(name).strip()}"
	issues = _item_issues_for_document(items, parent_key, "purchase_request_readiness")
	issues.extend(_line_quality_issues(items, parent_key, "purchase_request_readiness", require_schedule=True))
	issues.append(_issue(
		f"{parent_key}:future_step",
		"purchase_request_readiness",
		"info",
		"Future governed sourcing step",
		"Purchase Request downstream action remains guidance-only in this phase.",
		"Material Request",
		cstr(name).strip(),
		deferred_action="Future governed sourcing step",
	))
	return _context_payload("Material Request", cstr(name).strip(), issues)


def get_rfq_readiness_context(name: str) -> dict[str, object]:
	doc = _safe_get_doc("Request for Quotation", name)
	if not doc:
		return _context_payload("Request for Quotation", cstr(name).strip(), [])
	parent_key = f"Request for Quotation:{cstr(name).strip()}"
	issues = _supplier_issues_for_document(_child_rows(doc, "suppliers"), parent_key, "rfq_readiness")
	items = _child_rows(doc, "items")
	issues.extend(_item_issues_for_document(items, parent_key, "rfq_readiness"))
	issues.extend(_line_quality_issues(items, parent_key, "rfq_readiness", require_schedule=True))
	issues.append(_issue(
		f"{parent_key}:send_deferred",
		"rfq_readiness",
		"info",
		"Send remains deferred",
		"RFQ supplier communication remains preview/PDF/readiness only until governed send is approved.",
		"Request for Quotation",
		cstr(name).strip(),
		deferred_action="Governed RFQ send",
	))
	return _context_payload("Request for Quotation", cstr(name).strip(), issues)


def get_supplier_quotation_readiness_context(name: str) -> dict[str, object]:
	doc = _safe_get_doc("Supplier Quotation", name)
	if not doc:
		return _context_payload("Supplier Quotation", cstr(name).strip(), [])
	quotation = cstr(name).strip()
	parent_key = f"Supplier Quotation:{quotation}"
	issues: list[dict[str, object]] = []
	supplier = cstr(_value(doc, "supplier")).strip()
	if not supplier:
		issues.append(_issue(f"{parent_key}:supplier_missing", "supplier_quotation_readiness", "critical", "Supplier missing", "Supplier quotation needs a supplier before future comparison or award review.", "Supplier Quotation", quotation))
	else:
		issues.extend(_supplier_issues_for_document([{"supplier": supplier}], parent_key, "supplier_quotation_readiness"))
	items = _child_rows(doc, "items")
	issues.extend(_item_issues_for_document(items, parent_key, "supplier_quotation_readiness"))
	issues.extend(_line_quality_issues(items, parent_key, "supplier_quotation_readiness", require_rate=True))
	if _missing(_value(doc, "valid_till")):
		issues.append(_issue(f"{parent_key}:valid_till", "supplier_quotation_readiness", "warning", "Validity date missing", "Quotation validity is missing for future comparison readiness.", "Supplier Quotation", quotation))
	issues.append(_issue(f"{parent_key}:future_award", "supplier_quotation_readiness", "info", "Future governed award step", "Supplier selection and downstream document action remain deferred.", "Supplier Quotation", quotation, deferred_action="Future governed award step"))
	return _context_payload("Supplier Quotation", quotation, issues)


def get_purchase_order_readiness_context(name: str) -> dict[str, object]:
	doc = _safe_get_doc("Purchase Order", name)
	if not doc:
		return _context_payload("Purchase Order", cstr(name).strip(), [])
	po_name = cstr(name).strip()
	parent_key = f"Purchase Order:{po_name}"
	issues: list[dict[str, object]] = []
	supplier = cstr(_value(doc, "supplier")).strip()
	if not supplier:
		issues.append(_issue(f"{parent_key}:supplier_missing", "purchase_order_readiness", "critical", "Supplier missing", "Purchase Order needs supplier context before future release readiness.", "Purchase Order", po_name))
	else:
		issues.extend(_supplier_issues_for_document([{"supplier": supplier}], parent_key, "purchase_order_readiness"))
	items = _child_rows(doc, "items")
	issues.extend(_item_issues_for_document(items, parent_key, "purchase_order_readiness"))
	issues.extend(_line_quality_issues(items, parent_key, "purchase_order_readiness", require_rate=True, require_schedule=True))
	if _missing(_value(doc, "currency")):
		issues.append(_issue(f"{parent_key}:currency", "purchase_order_readiness", "warning", "Currency missing", "Purchase Order currency is required before future release readiness.", "Purchase Order", po_name))
	issues.append(_issue(f"{parent_key}:future_lifecycle", "purchase_order_readiness", "info", "Future governed order step", "Purchase Order release and supplier communication remain deferred.", "Purchase Order", po_name, deferred_action="Future governed order step"))
	return _context_payload("Purchase Order", po_name, issues)


def _top_visible_suppliers(limit: int = 6) -> list[dict[str, object]]:
	if not common.can_read("Supplier"):
		return []
	return common.get_list("Supplier", fields=["name", "supplier_name"], order_by="modified desc", limit=limit)


def _top_visible_items(limit: int = 6) -> list[dict[str, object]]:
	if not common.can_read("Item"):
		return []
	filters = []
	if common.has_field("Item", "is_purchase_item"):
		filters.append(["Item", "is_purchase_item", "=", 1])
	return common.get_list("Item", fields=["name", "item_name"], filters=filters, order_by="modified desc", limit=limit)


def _top_visible_documents(doctype: str, fields: list[str], limit: int = 4) -> list[dict[str, object]]:
	if not common.can_read(doctype):
		return []
	return common.get_list(doctype, fields=fields, order_by="modified desc", limit=limit)


def _issues_for_document_row(doctype: str, name: str) -> list[dict[str, object]]:
	if doctype == "Material Request":
		return get_purchase_request_readiness_context(name).get("issues") or []
	if doctype == "Request for Quotation":
		return get_rfq_readiness_context(name).get("issues") or []
	if doctype == "Supplier Quotation":
		return get_supplier_quotation_readiness_context(name).get("issues") or []
	if doctype == "Purchase Order":
		return get_purchase_order_readiness_context(name).get("issues") or []
	return []


def _visible_manager_issues(context: dict[str, object]) -> list[dict[str, object]]:
	issues: list[dict[str, object]] = []
	for supplier in _top_visible_suppliers():
		issues.extend(issue for issue in get_supplier_readiness_context(cstr(supplier.get("name"))).get("issues") or [] if issue.get("severity") != "ready")
	for item in _top_visible_items():
		issues.extend(issue for issue in get_item_buying_readiness_context(cstr(item.get("name"))).get("issues") or [] if issue.get("severity") != "ready")
	for doctype, fields in (
		("Material Request", ["name", "modified"]),
		("Request for Quotation", ["name", "modified"]),
		("Supplier Quotation", ["name", "supplier", "modified"]),
		("Purchase Order", ["name", "supplier", "modified"]),
	):
		for row in _top_visible_documents(doctype, fields):
			issues.extend(issue for issue in _issues_for_document_row(doctype, cstr(row.get("name"))) if issue.get("severity") != "ready")
	return _sort_issues(issues)[:ISSUE_LIMIT]


@frappe.whitelist()
def get_procurement_manager_readiness() -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	if not service.has_procurement_access(context):
		return {"visible": False, "state": service.restricted_state(), "groups": [], "issues": [], "summary": _summary([])}
	if not _is_manager(context):
		return {
			"visible": False,
			"state": common.ready_state(),
			"groups": [],
			"issues": [],
			"summary": _summary([]),
			"message": "Manager readiness queue is available to Purchase Manager roles.",
		}
	issues = _visible_manager_issues(context)
	groups: list[dict[str, object]] = []
	for group_key, group_label in GROUP_LABELS.items():
		group_issues = [issue for issue in issues if issue.get("group") == group_key]
		if group_issues:
			groups.append({"key": group_key, "label": group_label, "summary": _summary(group_issues), "issues": group_issues[:5]})
	return {
		"visible": True,
		"state": common.ready_state(),
		"groups": groups,
		"issues": issues,
		"summary": _summary(issues),
		"empty_message": "No readiness issues found for current checks.",
		"productized_only": True,
	}
