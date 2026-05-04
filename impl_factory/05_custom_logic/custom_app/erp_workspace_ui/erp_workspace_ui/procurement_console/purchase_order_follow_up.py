from __future__ import annotations

from collections import defaultdict
from typing import Any

import frappe
from frappe.utils import cstr, flt, getdate

from . import common


DETAIL_ROUTE = "procurement-console-po-follow-up"
FOLLOW_UP_ROW_LIMIT = 80
FOLLOW_UP_SCAN_LIMIT = 240
TERMINAL_STATUSES = ["Completed", "Closed", "Cancelled"]

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
	"modified",
]

PO_ITEM_FIELDS = [
	"name",
	"parent",
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


def purchase_order_follow_up_filters(filters: dict[str, str] | None = None, queue: str = "supplier_follow_up") -> list[list[object]]:
	applied = filters or {}
	conditions: list[list[object]] = []
	purchase_order = cstr(applied.get("purchase_order")).strip()
	if purchase_order:
		conditions.append(["Purchase Order", "name", "=", purchase_order])
	keyword = cstr(applied.get("keyword")).strip()
	if keyword:
		conditions.append(["Purchase Order", "name", "like", f"%{keyword}%"])
	supplier = cstr(applied.get("supplier")).strip()
	if supplier:
		conditions.append(["Purchase Order", "supplier", "=", supplier])
	company = cstr(applied.get("company")).strip()
	if company:
		conditions.append(["Purchase Order", "company", "=", company])
	status = cstr(applied.get("status")).strip()
	if status:
		conditions.append(["Purchase Order", "status", "=", status])
	date_start = cstr(applied.get("date_start")).strip()
	if date_start:
		conditions.append(["Purchase Order", "transaction_date", ">=", date_start])
	date_end = cstr(applied.get("date_end")).strip()
	if date_end:
		conditions.append(["Purchase Order", "transaction_date", "<=", date_end])

	conditions.extend(
		[
			["Purchase Order", "docstatus", "=", 1],
			["Purchase Order", "status", "not in", TERMINAL_STATUSES],
		]
	)
	if queue in {"due_soon", "overdue", "supplier_follow_up"}:
		conditions.append(["Purchase Order", "per_received", "<", 100])
	if queue == "partially_received":
		conditions.extend(
			[
				["Purchase Order", "per_received", ">", 0],
				["Purchase Order", "per_received", "<", 100],
			]
		)
	elif queue == "billing_visibility":
		conditions.extend(
			[
				["Purchase Order", "per_received", ">", 0],
				["Purchase Order", "per_billed", "<", 100],
			]
		)
	return conditions


def count_purchase_orders_due_soon() -> int:
	return len(_records_for_queue({}, "due_soon", FOLLOW_UP_SCAN_LIMIT))


def count_purchase_orders_overdue() -> int:
	return len(_records_for_queue({}, "overdue", FOLLOW_UP_SCAN_LIMIT))


def count_purchase_orders_partially_received() -> int:
	return len(_records_for_queue({}, "partially_received", FOLLOW_UP_SCAN_LIMIT))


def count_purchase_orders_not_billed_visibility() -> int:
	return len(_records_for_queue({}, "billing_visibility", FOLLOW_UP_SCAN_LIMIT))


def count_purchase_orders_supplier_follow_up() -> int:
	return len(_records_for_queue({}, "supplier_follow_up", FOLLOW_UP_SCAN_LIMIT))


def build_purchase_order_follow_up_summary() -> dict[str, int]:
	if not common.can_read("Purchase Order"):
		return {
			"due_soon": 0,
			"overdue": 0,
			"partially_received": 0,
			"billing_visibility": 0,
			"supplier_follow_up": 0,
		}
	supplier_records = _records_for_queue({}, "supplier_follow_up", FOLLOW_UP_SCAN_LIMIT)
	billing_records = _records_for_queue({}, "billing_visibility", FOLLOW_UP_SCAN_LIMIT)
	return {
		"due_soon": sum(1 for item in supplier_records if "due_soon" in set(item.get("reasons") or [])),
		"overdue": sum(1 for item in supplier_records if "overdue" in set(item.get("reasons") or [])),
		"partially_received": sum(1 for item in supplier_records if "partially_received" in set(item.get("reasons") or [])),
		"billing_visibility": len(billing_records),
		"supplier_follow_up": len(supplier_records),
	}


def build_purchase_orders_due_soon(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_payload(
		queue_key="purchase_orders_due_soon",
		title="Purchase Orders Due Soon",
		subtitle="Submitted purchase orders with open item lines due in the next seven days.",
		filters=filters or {},
		queue="due_soon",
	)


def build_purchase_orders_overdue(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_payload(
		queue_key="purchase_orders_overdue",
		title="Overdue Purchase Orders",
		subtitle="Submitted purchase orders with open item lines past required date.",
		filters=filters or {},
		queue="overdue",
	)


def build_purchase_orders_late_or_unreceived(filters: dict[str, str] | None = None) -> dict[str, object]:
	payload = build_purchase_orders_overdue(filters)
	payload["page"] = {"title": "Late Or Unreceived Purchase Orders", "key": "purchase_orders_late_or_unreceived"}
	payload["summary"]["title"] = "Late Or Unreceived Purchase Orders"
	payload["summary"]["subtitle"] = "Compatibility view for overdue purchase orders with open item lines."
	payload["controls"]["scopeChips"] = ["Purchase Order", "Read-only follow-up", "Compatibility alias"]
	return payload


def build_purchase_orders_partially_received(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_payload(
		queue_key="purchase_orders_partially_received",
		title="Partially Received Purchase Orders",
		subtitle="Submitted purchase orders where some quantity is received but fulfillment is not complete.",
		filters=filters or {},
		queue="partially_received",
	)


def build_purchase_orders_not_billed_visibility(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_payload(
		queue_key="purchase_orders_not_billed_visibility",
		title="Received Not Fully Billed",
		subtitle="Downstream billing posture for received purchase orders. Finance still owns invoice and payment work.",
		filters=filters or {},
		queue="billing_visibility",
	)


def build_purchase_orders_supplier_follow_up(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_payload(
		queue_key="purchase_orders_supplier_follow_up",
		title="Supplier Follow-up",
		subtitle="Purchase orders needing buyer follow-up because they are overdue, due soon, or partially received.",
		filters=filters or {},
		queue="supplier_follow_up",
	)


def _build_payload(queue_key: str, title: str, subtitle: str, filters: dict[str, str], queue: str) -> dict[str, object]:
	if not common.can_read("Purchase Order"):
		return _payload(
			queue_key,
			title,
			subtitle,
			filters,
			[],
			common.restricted_state(f"{title} restricted", "Purchase Order"),
		)

	rows = [_row_from_projection(record, queue_key) for record in _records_for_queue(filters, queue, FOLLOW_UP_ROW_LIMIT)]
	state = common.ready_state() if rows else common.empty_state(
		f"No {title.lower()}",
		"No visible purchase orders match the current follow-up filters.",
	)
	return _payload(queue_key, title, subtitle, filters, rows, state)


def _payload(
	queue_key: str,
	title: str,
	subtitle: str,
	filters: dict[str, str],
	rows: list[dict[str, object]],
	state: dict[str, object],
) -> dict[str, object]:
	options_by_name = {
		cstr(row.get("name")): {"return_queue": queue_key}
		for row in rows
		if cstr(row.get("name"))
	}
	return {
		"page": {"title": title, "key": queue_key},
		"summary": {
			"title": title,
			"subtitle": subtitle,
			"chips": [{"label": "Read-only PO follow-up"}],
		},
		"controls": {
			"fields": _control_fields(filters),
			"actions": common.standard_actions(),
			"scopeChips": ["Purchase Order", "Read-only follow-up"],
		},
		"metrics": [common.metric("Visible orders", len(rows), "Filtered purchase order records.")],
		"results": {
			"title": "Purchase order follow-up",
			"meta": f"{len(rows)} shown",
			"columns": [
				{"key": "order", "label": "Purchase Order"},
				{"key": "supplier", "label": "Supplier"},
				{"key": "follow_up", "label": "Follow-up"},
				{"key": "required_by", "label": "Required By"},
				{"key": "status", "label": "Status"},
				{"key": "received", "label": "Received"},
				{"key": "billed", "label": "Billed"},
			],
			"rows": rows,
			"rowActions": True,
			"state": state,
		},
		"action_targets": common.page_action_targets_for_rows(DETAIL_ROUTE, rows, options_by_name),
	}


def _records_for_queue(filters: dict[str, str], queue: str, limit: int) -> list[dict[str, object]]:
	if not common.can_read("Purchase Order"):
		return []
	records = common.get_list(
		"Purchase Order",
		fields=PO_FIELDS,
		filters=purchase_order_follow_up_filters(filters, queue=queue),
		order_by="schedule_date asc, modified desc",
		limit=limit,
	)
	if not records:
		return []

	line_map = _open_line_summary([cstr(record.get("name")) for record in records], limit * 8)
	projected: list[dict[str, object]] = []
	for record in records:
		name = cstr(record.get("name")).strip()
		summary = line_map.get(name) or _fallback_summary(record)
		next_date = summary.get("earliest_open_date")
		reasons = _follow_up_reasons(record, summary)
		if queue == "due_soon" and "due_soon" not in reasons:
			continue
		if queue == "overdue" and "overdue" not in reasons:
			continue
		if queue == "supplier_follow_up" and not reasons:
			continue
		projected.append({"record": record, "summary": summary, "reasons": reasons})

	projected.sort(key=lambda item: _sort_key(item, queue))
	return projected[:limit]


def _open_line_summary(po_names: list[str], limit: int) -> dict[str, dict[str, object]]:
	names = [name for name in po_names if name]
	if not names:
		return {}
	rows = _get_all(
		"Purchase Order Item",
		filters={"parent": ["in", names]},
		fields=PO_ITEM_FIELDS,
		order_by="schedule_date asc, expected_delivery_date asc, idx asc",
		limit=limit,
	)
	summary: dict[str, dict[str, object]] = defaultdict(lambda: {"open_lines": 0, "open_qty": 0.0, "earliest_open_date": "", "due_source": "Item schedule"})
	for row in rows:
		parent = cstr(row.get("parent")).strip()
		if not parent:
			continue
		qty = flt(row.get("qty"))
		received_qty = flt(row.get("received_qty"))
		remaining_qty = max(qty - received_qty, 0)
		if remaining_qty <= 0:
			continue
		item_due_date = _line_due_date(row)
		summary[parent]["open_lines"] = int(summary[parent].get("open_lines") or 0) + 1
		summary[parent]["open_qty"] = flt(summary[parent].get("open_qty")) + remaining_qty
		if item_due_date and (not summary[parent].get("earliest_open_date") or _date_key(item_due_date) < _date_key(summary[parent].get("earliest_open_date"))):
			summary[parent]["earliest_open_date"] = item_due_date
			summary[parent]["due_source"] = "Item expected date" if cstr(row.get("expected_delivery_date")).strip() else "Item schedule"
	return dict(summary)


def _fallback_summary(record: dict[str, object]) -> dict[str, object]:
	return {
		"open_lines": 0,
		"open_qty": 0.0,
		"earliest_open_date": cstr(record.get("schedule_date")).strip(),
		"due_source": "Header required date fallback",
	}


def _line_due_date(row: dict[str, object]) -> str:
	return cstr(row.get("expected_delivery_date") or row.get("schedule_date")).strip()


def _follow_up_reasons(record: dict[str, object], summary: dict[str, object]) -> list[str]:
	reasons: list[str] = []
	next_date = cstr(summary.get("earliest_open_date")).strip()
	if next_date:
		if _date_key(next_date) < _date_key(common.today_string()):
			reasons.append("overdue")
		elif _date_key(next_date) <= _date_key(common.date_days_from_now(7)):
			reasons.append("due_soon")
	if flt(record.get("per_received")) > 0 and flt(record.get("per_received")) < 100:
		reasons.append("partially_received")
	return reasons


def _row_from_projection(projection: dict[str, object], queue_key: str) -> dict[str, object]:
	record = projection["record"]
	summary = projection["summary"]
	reasons = projection["reasons"]
	name = cstr(record.get("name")).strip()
	return {
		"key": name,
		"name": name,
		"cells": {
			"order": {"value": name, "meta": record.get("company") or ""},
			"supplier": record.get("supplier_name") or record.get("supplier") or "-",
			"follow_up": _reason_label(reasons, summary),
			"required_by": cstr(summary.get("earliest_open_date") or record.get("schedule_date") or ""),
			"status": {
				"value": record.get("workflow_state") or record.get("status") or "-",
				"tone": "warning" if "overdue" in reasons else "",
			},
			"received": _percent(record.get("per_received")),
			"billed": _percent(record.get("per_billed")),
		},
		"actions": [{"key": "open_record", "label": "Open"}],
		"queue_key": queue_key,
	}


def _reason_label(reasons: list[str], summary: dict[str, object]) -> str:
	labels = {
		"overdue": "Overdue",
		"due_soon": "Due soon",
		"partially_received": "Partially received",
	}
	return ", ".join(labels.get(reason, reason) for reason in reasons) or cstr(summary.get("due_source") or "Follow-up")


def _sort_key(item: dict[str, object], queue: str) -> tuple[object, ...]:
	record = item["record"]
	summary = item["summary"]
	reasons = set(item.get("reasons") or [])
	priority = 0
	if "overdue" in reasons:
		priority = 0
	elif "due_soon" in reasons:
		priority = 1
	elif "partially_received" in reasons:
		priority = 2
	else:
		priority = 3
	if queue in {"due_soon", "overdue"}:
		priority = 0
	return (priority, _date_key(summary.get("earliest_open_date")), cstr(record.get("name")))


def _control_fields(filters: dict[str, str]) -> list[dict[str, object]]:
	return [
		{"key": "purchase_order", "label": "Purchase Order", "type": "link", "linkDoctype": "Purchase Order", "value": filters.get("purchase_order", ""), "placeholder": "Select purchase order"},
		{"key": "keyword", "label": "Search order ID or supplier", "type": "text", "value": filters.get("keyword", ""), "placeholder": "Search order ID or supplier"},
		{"key": "supplier", "label": "Supplier", "type": "link", "linkDoctype": "Supplier", "value": filters.get("supplier", ""), "placeholder": "Select supplier"},
		{
			"key": "status",
			"label": "Status",
			"type": "select",
			"value": filters.get("status", ""),
			"options": [
				{"label": "All", "value": ""},
				{"label": "To Receive and Bill", "value": "To Receive and Bill"},
				{"label": "To Receive", "value": "To Receive"},
				{"label": "To Bill", "value": "To Bill"},
				{"label": "On Hold", "value": "On Hold"},
			],
		},
		{"key": "date_start", "label": "PO Date From", "type": "date", "value": filters.get("date_start", "")},
		{"key": "date_end", "label": "PO Date To", "type": "date", "value": filters.get("date_end", "")},
	]


def _get_all(doctype: str, filters: dict[str, object] | None = None, fields: list[str] | None = None, order_by: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
	try:
		return list(
			frappe.get_all(
				doctype,
				filters=filters or {},
				fields=fields or ["name"],
				order_by=order_by,
				limit_page_length=limit or common.ROW_LIMIT,
			)
		)
	except Exception:
		return []


def _date_key(value: object) -> object:
	try:
		return getdate(value)
	except Exception:
		return getdate("2999-12-31")


def _percent(value: object) -> str:
	number = flt(value)
	if number.is_integer():
		return f"{int(number)}%"
	return f"{number:.1f}%"
