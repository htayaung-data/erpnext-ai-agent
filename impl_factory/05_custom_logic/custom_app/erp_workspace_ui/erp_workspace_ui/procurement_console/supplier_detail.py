from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from . import common, service


SUPPLIER_FIELDS = ["name", "supplier_name", "supplier_group", "disabled", "modified"]
PO_FIELDS = [
	"name",
	"supplier",
	"supplier_name",
	"transaction_date",
	"schedule_date",
	"status",
	"workflow_state",
	"per_received",
	"per_billed",
	"grand_total",
	"currency",
	"modified",
]
RFQ_SUPPLIER_FIELDS = ["parent", "supplier", "supplier_name", "quote_status", "modified"]
RFQ_FIELDS = ["name", "transaction_date", "schedule_date", "status", "docstatus", "modified"]
SUPPLIER_QUOTATION_FIELDS = [
	"name",
	"supplier",
	"supplier_name",
	"transaction_date",
	"valid_till",
	"status",
	"docstatus",
	"grand_total",
	"currency",
	"modified",
]


@frappe.whitelist()
def get_supplier_detail_context(supplier: str | None = None, name: str | None = None) -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	supplier_name = cstr(supplier or name).strip()
	if not service.has_procurement_access(context):
		return _state_payload(supplier_name, service.restricted_state(), context)
	if not supplier_name:
		return _state_payload(supplier_name, common.unavailable_state("Supplier required", "Open a supplier row to view this page."), context)
	if not common.can_read("Supplier"):
		return _state_payload(supplier_name, common.restricted_state("Supplier detail restricted", "Supplier"), context)

	record = _get_supplier(supplier_name)
	if not record:
		return _state_payload(supplier_name, common.unavailable_state("Supplier not found", "The requested supplier is not visible for this user."), context)

	return _detail_payload(
		record=record,
		context=context,
		recent_purchase_orders=_purchase_orders(supplier_name),
		rfqs=_rfqs(supplier_name),
		supplier_quotations=_supplier_quotations(supplier_name),
		contacts=_contacts(supplier_name),
	)


def _state_payload(supplier_name: str, state: dict[str, object], context: dict[str, object]) -> dict[str, object]:
	title = supplier_name or "Supplier Detail"
	return {
		"page": {"title": "Supplier Detail", "key": "supplier_detail", "supplier": supplier_name},
		"summary": {
			"kicker": "Procurement supplier",
			"title": title,
			"subtitle": state["detail"],
			"chips": [{"label": state["kind"], "tone": "blocker" if state["kind"] in {"restricted", "error"} else "neutral"}],
			"facts": [],
		},
		"controls": {"actions": _base_actions()},
		"detail": {
			"state": state,
			"recent_purchase_orders": _empty_table(),
			"open_purchase_orders": _empty_table(),
			"rfqs": _empty_table(),
			"supplier_quotations": _empty_table(),
			"contacts": _empty_table(),
		},
		"action_targets": _base_action_targets(),
		"context": {"role_variant": context.get("role_variant")},
	}


def _detail_payload(
	record: dict[str, object],
	context: dict[str, object],
	recent_purchase_orders: list[dict[str, object]],
	rfqs: list[dict[str, object]],
	supplier_quotations: list[dict[str, object]],
	contacts: list[dict[str, object]],
) -> dict[str, object]:
	name = cstr(record.get("name"))
	disabled = bool(record.get("disabled"))
	open_purchase_orders = [
		row for row in recent_purchase_orders
		if cstr(row.get("status")) not in {"Completed", "Closed", "Cancelled"} and flt(row.get("per_received")) < 100
	]
	actions = _base_actions()
	action_targets = _base_action_targets()
	return {
		"page": {"title": "Supplier Detail", "key": "supplier_detail", "supplier": name},
		"summary": {
			"kicker": "Supplier buying profile",
			"title": record.get("supplier_name") or name,
			"subtitle": "Read-only procurement view of supplier activity and buying context.",
			"chips": [
				{"label": "Disabled" if disabled else "Active", "tone": "danger" if disabled else "good"},
				{"label": "Read-only", "tone": "good"},
			],
			"facts": [
				{"label": "Supplier ID", "value": name, "meta": cstr(record.get("supplier_group") or "")},
				{"label": "Open POs", "value": len(open_purchase_orders), "meta": "Buyer follow-up posture"},
				{"label": "RFQs", "value": len(rfqs), "meta": "Visible supplier RFQ links"},
				{"label": "Quotations", "value": len(supplier_quotations), "meta": "Visible supplier quotations"},
			],
		},
		"controls": {"actions": actions},
		"detail": {
			"state": common.ready_state(),
			"supplier": {
				"name": name,
				"supplier_name": record.get("supplier_name") or name,
				"supplier_group": record.get("supplier_group") or "",
				"status": "Disabled" if disabled else "Active",
			},
			"recent_purchase_orders": _purchase_order_table(recent_purchase_orders, "Recent purchase orders"),
			"open_purchase_orders": _purchase_order_table(open_purchase_orders, "Open or overdue purchase orders"),
			"rfqs": _rfq_table(rfqs),
			"supplier_quotations": _supplier_quotation_table(supplier_quotations),
			"contacts": _contact_table(contacts),
		},
		"action_targets": action_targets,
		"context": {"role_variant": context.get("role_variant")},
	}


def _get_supplier(supplier_name: str) -> dict[str, object] | None:
	rows = common.get_list(
		"Supplier",
		fields=SUPPLIER_FIELDS,
		filters=[["Supplier", "name", "=", supplier_name]],
		order_by="modified desc",
		limit=1,
	)
	return dict(rows[0]) if rows else None


def _purchase_orders(supplier_name: str) -> list[dict[str, object]]:
	if not common.can_read("Purchase Order"):
		return []
	return common.get_list(
		"Purchase Order",
		fields=PO_FIELDS,
		filters=[["Purchase Order", "supplier", "=", supplier_name]],
		order_by="transaction_date desc, modified desc",
		limit=12,
	)


def _rfqs(supplier_name: str) -> list[dict[str, object]]:
	if not common.can_read("Request for Quotation"):
		return []
	child_rows = _get_all(
		"Request for Quotation Supplier",
		filters={"supplier": supplier_name},
		fields=RFQ_SUPPLIER_FIELDS,
		order_by="modified desc",
	)
	parent_names = [cstr(row.get("parent")).strip() for row in child_rows if cstr(row.get("parent")).strip()]
	if not parent_names:
		return []
	parent_by_name = {
		cstr(row.get("name")): row
		for row in common.get_list(
			"Request for Quotation",
			fields=RFQ_FIELDS,
			filters=[["Request for Quotation", "name", "in", parent_names]],
			order_by="transaction_date desc, modified desc",
			limit=12,
		)
	}
	payload = []
	for child in child_rows:
		parent = parent_by_name.get(cstr(child.get("parent")))
		if not parent:
			continue
		row = dict(parent)
		row["quote_status"] = child.get("quote_status")
		payload.append(row)
	return payload[:12]


def _supplier_quotations(supplier_name: str) -> list[dict[str, object]]:
	if not common.can_read("Supplier Quotation"):
		return []
	return common.get_list(
		"Supplier Quotation",
		fields=SUPPLIER_QUOTATION_FIELDS,
		filters=[["Supplier Quotation", "supplier", "=", supplier_name]],
		order_by="transaction_date desc, modified desc",
		limit=12,
	)


def _contacts(supplier_name: str) -> list[dict[str, object]]:
	if not common.can_read("Contact"):
		return []
	links = _get_all(
		"Dynamic Link",
		filters={"link_doctype": "Supplier", "link_name": supplier_name, "parenttype": "Contact"},
		fields=["parent"],
		order_by="modified desc",
	)
	contact_names = [cstr(row.get("parent")).strip() for row in links if cstr(row.get("parent")).strip()]
	if not contact_names:
		return []
	return common.get_list(
		"Contact",
		fields=["name", "first_name", "last_name", "email_id", "phone", "mobile_no", "modified"],
		filters=[["Contact", "name", "in", contact_names]],
		order_by="modified desc",
		limit=8,
	)


def _get_all(doctype: str, filters: dict[str, object] | None = None, fields: list[str] | None = None, order_by: str | None = None) -> list[dict[str, Any]]:
	try:
		return list(
			frappe.get_all(
				doctype,
				filters=filters or {},
				fields=fields or ["name"],
				order_by=order_by,
				limit_page_length=common.ROW_LIMIT,
			)
		)
	except Exception:
		return []


def _base_actions() -> list[dict[str, object]]:
	return [
		{"key": "back_to_suppliers", "title": "Back to suppliers", "label": "Back to suppliers", "variant": "secondary", "category": "navigation", "icon": "arrow-left"},
		{"key": "refresh", "title": "Refresh", "label": "Refresh", "variant": "secondary", "icon": "refresh"},
	]


def _base_action_targets() -> dict[str, object]:
	return {"back_to_suppliers": {"kind": "worklist", "queue_key": "supplier_directory"}}



def _empty_table() -> dict[str, object]:
	return {"columns": [], "rows": [], "state": common.empty_state()}


def _purchase_order_table(rows: list[dict[str, object]], title: str) -> dict[str, object]:
	return {
		"title": title,
		"columns": [
			{"key": "purchase_order", "label": "Purchase Order"},
			{"key": "status", "label": "Status"},
			{"key": "required_by", "label": "Required By"},
			{"key": "received", "label": "Received"},
			{"key": "billed", "label": "Billed"},
			{"key": "total", "label": "Total"},
		],
		"rows": [
			{
				"key": cstr(row.get("name")),
				"cells": {
					"purchase_order": {
						"value": row.get("name") or "-",
						"route": "procurement-console-po-follow-up",
						"route_parts": [row.get("name") or ""],
					},
					"status": row.get("workflow_state") or row.get("status") or "-",
					"required_by": cstr(row.get("schedule_date") or ""),
					"received": _percent(row.get("per_received")),
					"billed": _percent(row.get("per_billed")),
					"total": _money(row.get("grand_total"), row.get("currency")),
				},
			}
			for row in rows
		],
		"state": common.ready_state() if rows else common.empty_state("No visible purchase orders", "No visible Purchase Orders are linked to this supplier."),
	}


def _rfq_table(rows: list[dict[str, object]]) -> dict[str, object]:
	return {
		"title": "RFQs",
		"columns": [
			{"key": "rfq", "label": "RFQ"},
			{"key": "status", "label": "Status"},
			{"key": "quote_status", "label": "Supplier Response"},
			{"key": "date", "label": "Date"},
			{"key": "required_by", "label": "Required By"},
		],
		"rows": [
			{
				"key": cstr(row.get("name")),
				"cells": {
					"rfq": row.get("name") or "-",
					"status": row.get("status") or "-",
					"quote_status": row.get("quote_status") or "-",
					"date": cstr(row.get("transaction_date") or ""),
					"required_by": cstr(row.get("schedule_date") or ""),
				},
			}
			for row in rows
		],
		"state": common.ready_state() if rows else common.empty_state("No visible RFQs", "No visible RFQs are linked to this supplier."),
	}


def _supplier_quotation_table(rows: list[dict[str, object]]) -> dict[str, object]:
	return {
		"title": "Supplier quotations",
		"columns": [
			{"key": "quotation", "label": "Supplier Quotation"},
			{"key": "status", "label": "Status"},
			{"key": "date", "label": "Date"},
			{"key": "valid_till", "label": "Valid Till"},
			{"key": "total", "label": "Total"},
		],
		"rows": [
			{
				"key": cstr(row.get("name")),
				"cells": {
					"quotation": row.get("name") or "-",
					"status": row.get("status") or "-",
					"date": cstr(row.get("transaction_date") or ""),
					"valid_till": cstr(row.get("valid_till") or ""),
					"total": _money(row.get("grand_total"), row.get("currency")),
				},
			}
			for row in rows
		],
		"state": common.ready_state() if rows else common.empty_state("No visible supplier quotations", "No visible Supplier Quotations are linked to this supplier."),
	}


def _contact_table(rows: list[dict[str, object]]) -> dict[str, object]:
	return {
		"title": "Buying contacts",
		"columns": [
			{"key": "contact", "label": "Contact"},
			{"key": "email", "label": "Email"},
			{"key": "phone", "label": "Phone"},
		],
		"rows": [
			{
				"key": cstr(row.get("name")),
				"cells": {
					"contact": " ".join(part for part in [cstr(row.get("first_name")).strip(), cstr(row.get("last_name")).strip()] if part) or row.get("name") or "-",
					"email": row.get("email_id") or "-",
					"phone": row.get("mobile_no") or row.get("phone") or "-",
				},
			}
			for row in rows
		],
		"state": common.ready_state() if rows else common.empty_state("No visible buying contacts", "No visible Contact records are linked to this supplier."),
	}


def _percent(value: object) -> str:
	return f"{flt(value):.0f}%"


def _money(value: object, currency: object) -> str:
	amount = flt(value)
	currency_label = cstr(currency).strip()
	if amount.is_integer():
		amount_text = f"{int(amount):,}"
	else:
		amount_text = f"{amount:,.2f}"
	return f"{amount_text} {currency_label}".strip()
