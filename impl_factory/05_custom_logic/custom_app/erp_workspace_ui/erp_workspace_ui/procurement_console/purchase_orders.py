from __future__ import annotations

from frappe.utils import cstr

from . import common


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

TERMINAL_STATUSES = ["Completed", "Closed", "Cancelled"]
PENDING_PURCHASE_APPROVAL_STATE = "Pending Purchase Approval"


def purchase_order_filters(filters: dict[str, str] | None = None, queue: str = "directory") -> list[list[object]]:
	applied = filters or {}
	conditions: list[list[object]] = []
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

	if queue == "pending_approval":
		conditions.append(["Purchase Order", "workflow_state", "=", PENDING_PURCHASE_APPROVAL_STATE])
	elif queue == "open":
		conditions.extend(
			[
				["Purchase Order", "docstatus", "=", 1],
				["Purchase Order", "status", "not in", TERMINAL_STATUSES],
			]
		)
	elif queue == "late":
		conditions.extend(
			[
				["Purchase Order", "docstatus", "=", 1],
				["Purchase Order", "status", "not in", TERMINAL_STATUSES],
				["Purchase Order", "schedule_date", "<", common.today_string()],
				["Purchase Order", "per_received", "<", 100],
			]
		)
	return conditions


def count_purchase_orders_open() -> int:
	if not common.can_read("Purchase Order"):
		return 0
	return common.count("Purchase Order", filters=purchase_order_filters(queue="open"))


def count_purchase_order_directory() -> int:
	if not common.can_read("Purchase Order"):
		return 0
	return common.count("Purchase Order", filters=purchase_order_filters(queue="directory"))


def count_purchase_orders_pending_approval() -> int:
	if not common.can_read("Purchase Order"):
		return 0
	return common.count("Purchase Order", filters=purchase_order_filters(queue="pending_approval"))


def count_purchase_orders_late_or_unreceived() -> int:
	if not common.can_read("Purchase Order"):
		return 0
	return common.count("Purchase Order", filters=purchase_order_filters(queue="late"))


def build_purchase_order_directory(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_purchase_order_payload(
		queue_key="purchase_order_directory",
		title="Purchase Orders",
		subtitle="Visible purchase orders for buyer follow-up.",
		filters=filters or {},
		queue="directory",
	)


def build_purchase_orders_pending_approval(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_purchase_order_payload(
		queue_key="purchase_orders_pending_approval",
		title="Purchase Orders Pending Approval",
		subtitle="Purchase orders currently waiting for purchase approval. This is visibility only in Phase 1.",
		filters=filters or {},
		queue="pending_approval",
	)


def build_purchase_orders_open(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_purchase_order_payload(
		queue_key="purchase_orders_open",
		title="Open Purchase Orders",
		subtitle="Submitted purchase orders that are still active.",
		filters=filters or {},
		queue="open",
	)


def build_purchase_orders_late_or_unreceived(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_purchase_order_payload(
		queue_key="purchase_orders_late_or_unreceived",
		title="Late Or Unreceived Purchase Orders",
		subtitle="Open purchase orders past required date and not fully received.",
		filters=filters or {},
		queue="late",
	)


def _build_purchase_order_payload(
	queue_key: str,
	title: str,
	subtitle: str,
	filters: dict[str, str],
	queue: str,
) -> dict[str, object]:
	if not common.can_read("Purchase Order"):
		return _purchase_order_payload(queue_key, title, subtitle, filters, [], common.restricted_state(f"{title} restricted", "Purchase Order"))

	rows = _purchase_order_rows(filters, queue)
	state = common.ready_state() if rows else common.empty_state(
		f"No {title.lower()}",
		"No visible purchase orders match the current filters.",
	)
	return _purchase_order_payload(queue_key, title, subtitle, filters, rows, state)


def _purchase_order_rows(filters: dict[str, str], queue: str) -> list[dict[str, object]]:
	records = common.get_list(
		"Purchase Order",
		fields=PO_FIELDS,
		filters=purchase_order_filters(filters, queue=queue),
		order_by="transaction_date desc, modified desc",
	)
	rows: list[dict[str, object]] = []
	for record in records:
		name = cstr(record.get("name")).strip()
		if not name:
			continue
		rows.append(
			{
				"key": name,
				"name": name,
				"cells": {
					"order": {"value": name, "meta": record.get("supplier_name") or record.get("supplier") or ""},
					"company": record.get("company") or "-",
					"required_by": cstr(record.get("schedule_date") or ""),
					"status": {
						"value": record.get("workflow_state") or record.get("status") or "-",
						"tone": "warning" if record.get("workflow_state") == PENDING_PURCHASE_APPROVAL_STATE else "",
					},
					"received": f"{record.get('per_received') or 0}%",
					"billed": f"{record.get('per_billed') or 0}%",
				},
				"actions": [{"key": "open_record", "label": "Open"}],
			}
		)
	return rows


def _purchase_order_payload(
	queue_key: str,
	title: str,
	subtitle: str,
	filters: dict[str, str],
	rows: list[dict[str, object]],
	state: dict[str, object],
) -> dict[str, object]:
	return {
		"page": {"title": title, "key": queue_key},
		"summary": {
			"title": title,
			"subtitle": subtitle,
			"chips": [{"label": "No approval actions"}],
		},
		"controls": {
			"fields": [
				{"key": "keyword", "label": "Search", "type": "text", "value": filters.get("keyword", ""), "placeholder": "Purchase Order ID"},
				{"key": "supplier", "label": "Supplier", "type": "text", "value": filters.get("supplier", "")},
				{"key": "company", "label": "Company", "type": "text", "value": filters.get("company", "")},
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
						{"label": "Completed", "value": "Completed"},
						{"label": "Closed", "value": "Closed"},
					],
				},
				{"key": "date_start", "label": "From", "type": "date", "value": filters.get("date_start", "")},
				{"key": "date_end", "label": "To", "type": "date", "value": filters.get("date_end", "")},
			],
			"actions": common.standard_actions(),
			"scopeChips": ["Purchase Order", "Visibility only"],
		},
		"metrics": [
			common.metric("Visible orders", len(rows), "Filtered purchase order records."),
		],
		"results": {
			"title": "Purchase order records",
			"meta": f"{len(rows)} shown",
			"columns": [
				{"key": "order", "label": "Purchase Order"},
				{"key": "company", "label": "Company"},
				{"key": "required_by", "label": "Required By"},
				{"key": "status", "label": "Status"},
				{"key": "received", "label": "Received"},
				{"key": "billed", "label": "Billed"},
			],
			"rows": rows,
			"rowActions": True,
			"state": state,
		},
		"action_targets": common.action_targets_for_rows("Purchase Order", rows),
	}
