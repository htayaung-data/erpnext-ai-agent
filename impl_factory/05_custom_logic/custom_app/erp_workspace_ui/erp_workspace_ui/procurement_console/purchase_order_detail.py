from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from . import common, service


PO_FIELDS = [
	"name",
	"supplier",
	"supplier_name",
	"company",
	"transaction_date",
	"schedule_date",
	"status",
	"workflow_state",
	"per_received",
	"per_billed",
	"grand_total",
	"currency",
]

PO_ITEM_FIELDS = [
	"name",
	"item_code",
	"item_name",
	"schedule_date",
	"expected_delivery_date",
	"qty",
	"received_qty",
	"warehouse",
	"material_request",
	"supplier_quotation",
]

PR_ITEM_FIELDS = [
	"parent",
	"item_code",
	"qty",
	"received_qty",
	"rejected_qty",
	"warehouse",
	"billed_amt",
]

PI_ITEM_FIELDS = [
	"parent",
	"item_code",
	"qty",
	"amount",
	"purchase_receipt",
]


@frappe.whitelist()
def get_purchase_order_follow_up_detail_context(
	purchase_order: str | None = None,
	name: str | None = None,
	return_queue: str | None = None,
) -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	po_name = cstr(purchase_order or name).strip()
	if not service.has_procurement_access(context):
		return _state_payload(po_name, service.restricted_state(), return_queue)
	if not po_name:
		return _state_payload(po_name, common.unavailable_state("Purchase Order required", "Open a purchase order follow-up row to view this page."), return_queue)
	if not common.can_read("Purchase Order"):
		return _state_payload(po_name, common.restricted_state("Purchase Order follow-up restricted", "Purchase Order"), return_queue)

	record = _get_po(po_name)
	if not record:
		return _state_payload(po_name, common.unavailable_state("Purchase Order not found", "The requested purchase order is not visible for this user."), return_queue)

	items = _item_rows(po_name)
	receipts = _receipt_rows(po_name)
	invoices = _invoice_rows(po_name)
	return _detail_payload(record, items, receipts, invoices, return_queue)


def _state_payload(po_name: str, state: dict[str, object], return_queue: str | None) -> dict[str, object]:
	title = po_name or "Purchase Order Follow-up"
	return {
		"page": {"title": "Purchase Order Follow-up", "key": "purchase_order_follow_up", "purchase_order": po_name},
		"summary": {
			"kicker": "Procurement Console",
			"title": title,
			"subtitle": state["detail"],
			"chips": [{"label": state["kind"], "tone": "blocker" if state["kind"] in {"restricted", "error"} else "neutral"}],
			"facts": [],
		},
		"controls": {"actions": _base_actions(return_queue)},
		"detail": {
			"state": state,
			"items": {"columns": [], "rows": []},
			"downstream": {"receipts": _visibility_state("Purchase Receipt"), "billing": _visibility_state("Purchase Invoice")},
		},
		"action_targets": _base_action_targets(return_queue),
	}


def _detail_payload(
	record: dict[str, object],
	items: list[dict[str, object]],
	receipts: list[dict[str, object]],
	invoices: list[dict[str, object]],
	return_queue: str | None,
) -> dict[str, object]:
	name = cstr(record.get("name"))
	receipt_qty = sum(flt(row.get("qty")) for row in receipts)
	invoice_amount = sum(flt(row.get("amount")) for row in invoices)
	return {
		"page": {"title": "Purchase Order Follow-up", "key": "purchase_order_follow_up", "purchase_order": name},
		"summary": {
			"kicker": "Purchase Order follow-up",
			"title": name,
			"subtitle": "Read-only buyer follow-up view. Warehouse and Finance execution actions are not exposed.",
			"chips": [{"label": "Read-only", "tone": "good"}, {"label": record.get("workflow_state") or record.get("status") or "Status", "tone": "pending"}],
			"facts": [
				{"label": "Supplier", "value": record.get("supplier_name") or record.get("supplier") or "--", "meta": record.get("company") or ""},
				{"label": "Required By", "value": cstr(record.get("schedule_date") or "--"), "meta": "Header date"},
				{"label": "Received", "value": _percent(record.get("per_received")), "meta": "Purchase posture"},
				{"label": "Billed", "value": _percent(record.get("per_billed")), "meta": "Finance visibility"},
			],
		},
		"controls": {"actions": _base_actions(return_queue)},
		"detail": {
			"state": common.ready_state(),
			"header": {
				"supplier": record.get("supplier_name") or record.get("supplier") or "",
				"required_date": cstr(record.get("schedule_date") or ""),
				"status": record.get("workflow_state") or record.get("status") or "",
				"received_percent": _percent(record.get("per_received")),
				"billed_percent": _percent(record.get("per_billed")),
				"total": _money(record.get("grand_total"), record.get("currency")),
			},
			"items": {
				"title": "Item lines",
				"columns": [
					{"key": "item", "label": "Item"},
					{"key": "qty", "label": "Qty"},
					{"key": "received_qty", "label": "Received"},
					{"key": "remaining_qty", "label": "Remaining"},
					{"key": "warehouse", "label": "Warehouse"},
					{"key": "due_date", "label": "Line Due"},
					{"key": "references", "label": "References"},
				],
				"rows": items,
				"state": common.ready_state() if items else common.empty_state("No visible item lines", "No purchase order item lines are visible."),
			},
			"downstream": {
				"receipts": {
					"state": _downstream_state("Purchase Receipt", receipts),
					"metric": f"{len({row.get('parent') for row in receipts if row.get('parent')})} receipt documents",
					"detail": f"{_quantity(receipt_qty)} received quantity shown from visible receipt lines.",
					"rows": receipts[:common.ROW_LIMIT],
				},
				"billing": {
					"state": _downstream_state("Purchase Invoice", invoices),
					"metric": f"{len({row.get('parent') for row in invoices if row.get('parent')})} invoice documents",
					"detail": f"{_money(invoice_amount, record.get('currency'))} visible invoice amount linked to this order.",
					"rows": invoices[:common.ROW_LIMIT],
				},
			},
		},
		"action_targets": _base_action_targets(return_queue),
	}


def _get_po(po_name: str) -> dict[str, object] | None:
	rows = common.get_list(
		"Purchase Order",
		fields=PO_FIELDS,
		filters=[["Purchase Order", "name", "=", po_name]],
		limit=1,
	)
	return dict(rows[0]) if rows else None


def _item_rows(po_name: str) -> list[dict[str, object]]:
	rows = _get_all("Purchase Order Item", filters={"parent": po_name}, fields=PO_ITEM_FIELDS, order_by="schedule_date asc, idx asc")
	payload = []
	for row in rows:
		qty = flt(row.get("qty"))
		received = flt(row.get("received_qty"))
		remaining = max(qty - received, 0)
		refs = [cstr(row.get("material_request")).strip(), cstr(row.get("supplier_quotation")).strip()]
		payload.append(
			{
				"key": cstr(row.get("name") or row.get("item_code")),
				"cells": {
					"item": {"value": row.get("item_code") or "-", "meta": row.get("item_name") or ""},
					"qty": _quantity(qty),
					"received_qty": _quantity(received),
					"remaining_qty": _quantity(remaining),
					"warehouse": row.get("warehouse") or "-",
					"due_date": cstr(row.get("expected_delivery_date") or row.get("schedule_date") or ""),
					"references": ", ".join([ref for ref in refs if ref]) or "-",
				},
			}
		)
	return payload


def _receipt_rows(po_name: str) -> list[dict[str, object]]:
	if not common.can_read("Purchase Receipt"):
		return []
	return _get_all("Purchase Receipt Item", filters={"purchase_order": po_name}, fields=PR_ITEM_FIELDS, order_by="modified desc")


def _invoice_rows(po_name: str) -> list[dict[str, object]]:
	if not common.can_read("Purchase Invoice"):
		return []
	return _get_all("Purchase Invoice Item", filters={"purchase_order": po_name}, fields=PI_ITEM_FIELDS, order_by="modified desc")


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


def _base_actions(return_queue: str | None) -> list[dict[str, object]]:
	return [
		{"key": "back_to_queue", "title": "Back to queue", "label": "Back to queue", "variant": "secondary", "category": "navigation"},
		{"key": "refresh", "title": "Refresh", "label": "Refresh", "variant": "secondary"},
	]


def _base_action_targets(return_queue: str | None) -> dict[str, object]:
	queue_key = cstr(return_queue).strip() or "purchase_orders_supplier_follow_up"
	return {"back_to_queue": {"kind": "worklist", "queue_key": queue_key}}


def _visibility_state(doctype: str) -> dict[str, object]:
	if common.can_read(doctype):
		return common.empty_state(f"No visible {doctype}", f"No visible {doctype} records are linked to this order.")
	return common.restricted_state(f"{doctype} visibility restricted", doctype)


def _downstream_state(doctype: str, rows: list[dict[str, object]]) -> dict[str, object]:
	if not common.can_read(doctype):
		return common.restricted_state(f"{doctype} visibility restricted", doctype)
	if rows:
		return common.ready_state()
	return common.empty_state(f"No visible {doctype}", f"No visible {doctype} records are linked to this order.")


def _quantity(value: object) -> str:
	number = flt(value)
	if number.is_integer():
		return str(int(number))
	return f"{number:,.2f}"


def _percent(value: object) -> str:
	number = flt(value)
	if number.is_integer():
		return f"{int(number)}%"
	return f"{number:.1f}%"


def _money(value: object, currency: object) -> str:
	amount = flt(value)
	code = cstr(currency).strip()
	if code:
		return f"{code} {amount:,.2f}"
	return f"{amount:,.2f}"
