from __future__ import annotations

from collections import defaultdict
from typing import Any

import frappe
from frappe.utils import cstr, flt

from . import common


RFQ_FIELDS = [
	"name",
	"company",
	"transaction_date",
	"schedule_date",
	"status",
	"docstatus",
	"modified",
]

RFQ_SUPPLIER_FIELDS = ["parent", "supplier", "supplier_name", "quote_status"]

SQ_FIELDS = [
	"name",
	"supplier",
	"supplier_name",
	"company",
	"status",
	"transaction_date",
	"valid_till",
	"currency",
	"grand_total",
	"docstatus",
	"modified",
]

RFQ_QUOTE_STATUS_DOCTYPE = "Request for Quotation Supplier"


def quote_status_available() -> bool:
	return common.has_field(RFQ_QUOTE_STATUS_DOCTYPE, "quote_status")


def rfq_filters(filters: dict[str, str] | None = None, queue: str = "directory") -> list[list[object]]:
	applied = filters or {}
	conditions: list[list[object]] = []
	keyword = cstr(applied.get("keyword")).strip()
	if keyword:
		conditions.append(["Request for Quotation", "name", "like", f"%{keyword}%"])
	company = cstr(applied.get("company")).strip()
	if company:
		conditions.append(["Request for Quotation", "company", "=", company])
	status = cstr(applied.get("status")).strip()
	if status:
		conditions.append(["Request for Quotation", "status", "=", status])
	date_start = cstr(applied.get("date_start")).strip()
	if date_start:
		conditions.append(["Request for Quotation", "transaction_date", ">=", date_start])
	date_end = cstr(applied.get("date_end")).strip()
	if date_end:
		conditions.append(["Request for Quotation", "transaction_date", "<=", date_end])
	if queue in {"awaiting_response", "partially_quoted"}:
		conditions.append(["Request for Quotation", "docstatus", "=", 1])
	return conditions


def supplier_quotation_filters(filters: dict[str, str] | None = None, queue: str = "directory") -> list[list[object]]:
	applied = filters or {}
	conditions: list[list[object]] = []
	keyword = cstr(applied.get("keyword")).strip()
	if keyword:
		conditions.append(["Supplier Quotation", "name", "like", f"%{keyword}%"])
	supplier = cstr(applied.get("supplier")).strip()
	if supplier:
		conditions.append(["Supplier Quotation", "supplier", "=", supplier])
	company = cstr(applied.get("company")).strip()
	if company:
		conditions.append(["Supplier Quotation", "company", "=", company])
	status = cstr(applied.get("status")).strip()
	if status:
		conditions.append(["Supplier Quotation", "status", "=", status])
	date_start = cstr(applied.get("date_start")).strip()
	if date_start:
		conditions.append(["Supplier Quotation", "transaction_date", ">=", date_start])
	date_end = cstr(applied.get("date_end")).strip()
	if date_end:
		conditions.append(["Supplier Quotation", "transaction_date", "<=", date_end])
	if queue == "to_compare":
		conditions.extend(
			[
				["Supplier Quotation", "docstatus", "=", 1],
				["Supplier Quotation", "status", "not in", ["Cancelled", "Stopped"]],
			]
		)
	elif queue == "expiring":
		conditions.extend(
			[
				["Supplier Quotation", "docstatus", "=", 1],
				["Supplier Quotation", "status", "not in", ["Cancelled", "Stopped"]],
				["Supplier Quotation", "valid_till", ">=", common.today_string()],
				["Supplier Quotation", "valid_till", "<=", common.date_days_from_now(7)],
			]
		)
	return conditions


def count_rfq_directory() -> int:
	if not common.can_read("Request for Quotation"):
		return 0
	return common.count("Request for Quotation", filters=[])


def count_rfqs_awaiting_supplier_response() -> int:
	payload = _rfq_names_by_quote_status("Pending")
	return len(payload)


def count_rfqs_partially_quoted() -> int:
	return len(_partially_quoted_rfq_names())


def count_supplier_quotation_directory() -> int:
	if not common.can_read("Supplier Quotation"):
		return 0
	return common.count("Supplier Quotation", filters=[])


def count_supplier_quotations_to_compare() -> int:
	if not common.can_read("Supplier Quotation"):
		return 0
	return common.count("Supplier Quotation", filters=supplier_quotation_filters(queue="to_compare"))


def count_supplier_quotations_expiring() -> int:
	if not common.can_read("Supplier Quotation"):
		return 0
	return common.count("Supplier Quotation", filters=supplier_quotation_filters(queue="expiring"))


def build_rfq_directory(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_rfq_payload(
		queue_key="rfq_directory",
		title="RFQs",
		subtitle="Read-only Request for Quotation records for sourcing follow-up.",
		filters=filters or {},
		queue="directory",
	)


def build_rfqs_awaiting_supplier_response(filters: dict[str, str] | None = None) -> dict[str, object]:
	if not quote_status_available():
		return _rfq_unavailable_payload(
			"rfqs_awaiting_supplier_response",
			"RFQs Awaiting Supplier Response",
			"Supplier response tracking is unavailable because RFQ supplier quote status is not configured.",
			filters or {},
		)
	return _build_rfq_payload(
		queue_key="rfqs_awaiting_supplier_response",
		title="RFQs Awaiting Supplier Response",
		subtitle="Submitted RFQs with at least one supplier still pending response.",
		filters=filters or {},
		queue="awaiting_response",
	)


def build_rfqs_partially_quoted(filters: dict[str, str] | None = None) -> dict[str, object]:
	if not quote_status_available():
		return _rfq_unavailable_payload(
			"rfqs_partially_quoted",
			"Partially Quoted RFQs",
			"Partial response tracking is unavailable because RFQ supplier quote status is not configured.",
			filters or {},
		)
	return _build_rfq_payload(
		queue_key="rfqs_partially_quoted",
		title="Partially Quoted RFQs",
		subtitle="Submitted RFQs with a mix of received and pending supplier quotation status.",
		filters=filters or {},
		queue="partially_quoted",
	)


def build_supplier_quotation_directory(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_supplier_quotation_payload(
		queue_key="supplier_quotation_directory",
		title="Supplier Quotations",
		subtitle="Read-only supplier quotation records for sourcing review.",
		filters=filters or {},
		queue="directory",
	)


def build_supplier_quotations_to_compare(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_supplier_quotation_payload(
		queue_key="supplier_quotations_to_compare",
		title="Supplier Quotations To Compare",
		subtitle="Submitted supplier quotations available for comparison review.",
		filters=filters or {},
		queue="to_compare",
	)


def build_supplier_quotations_expiring(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_supplier_quotation_payload(
		queue_key="supplier_quotations_expiring",
		title="Expiring Supplier Quotations",
		subtitle="Submitted supplier quotations expiring within the next seven days.",
		filters=filters or {},
		queue="expiring",
	)


def _build_rfq_payload(queue_key: str, title: str, subtitle: str, filters: dict[str, str], queue: str) -> dict[str, object]:
	if not common.can_read("Request for Quotation"):
		return _rfq_payload(queue_key, title, subtitle, filters, [], common.restricted_state(f"{title} restricted", "Request for Quotation"))

	rows = _rfq_rows(filters, queue)
	state = common.ready_state() if rows else common.empty_state(f"No {title.lower()}", "No visible RFQs match the current filters.")
	return _rfq_payload(queue_key, title, subtitle, filters, rows, state)


def _rfq_rows(filters: dict[str, str], queue: str) -> list[dict[str, object]]:
	records = common.get_list(
		"Request for Quotation",
		fields=RFQ_FIELDS,
		filters=rfq_filters(filters, queue=queue),
		order_by="transaction_date desc, modified desc",
	)
	if queue == "awaiting_response":
		allowed_names = _rfq_names_by_quote_status("Pending")
		records = [record for record in records if record.get("name") in allowed_names]
	elif queue == "partially_quoted":
		allowed_names = _partially_quoted_rfq_names()
		records = [record for record in records if record.get("name") in allowed_names]

	supplier_map = _supplier_status_map([cstr(record.get("name")) for record in records])
	rows: list[dict[str, object]] = []
	for record in records:
		name = cstr(record.get("name")).strip()
		if not name:
			continue
		summary = supplier_map.get(name, {"Pending": 0, "Received": 0})
		rows.append(
			{
				"key": name,
				"name": name,
				"cells": {
					"rfq": {"value": name, "meta": record.get("company") or ""},
					"date": cstr(record.get("transaction_date") or ""),
					"required_by": cstr(record.get("schedule_date") or ""),
					"status": record.get("status") or "-",
					"pending": summary.get("Pending", 0),
					"received": summary.get("Received", 0),
				},
				"actions": [{"key": "open_record", "label": "Open"}],
			}
		)
	return rows


def _rfq_payload(
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
			"chips": [{"label": "Read-only sourcing"}],
		},
		"controls": {
			"fields": _rfq_control_fields(filters),
			"actions": common.standard_actions(),
			"scopeChips": ["Request for Quotation", "No send/email action"],
		},
		"metrics": [common.metric("Visible RFQs", len(rows), "Filtered RFQ records.")],
		"results": {
			"title": "RFQ records",
			"meta": f"{len(rows)} shown",
			"columns": [
				{"key": "rfq", "label": "RFQ"},
				{"key": "date", "label": "Date"},
				{"key": "required_by", "label": "Required By"},
				{"key": "status", "label": "Status"},
				{"key": "pending", "label": "Pending"},
				{"key": "received", "label": "Received"},
			],
			"rows": rows,
			"rowActions": True,
			"state": state,
		},
		"action_targets": common.action_targets_for_rows("Request for Quotation", rows),
	}


def _rfq_unavailable_payload(queue_key: str, title: str, detail: str, filters: dict[str, str]) -> dict[str, object]:
	return _rfq_payload(
		queue_key,
		title,
		detail,
		filters,
		[],
		common.unavailable_state(title, detail),
	)


def _build_supplier_quotation_payload(
	queue_key: str,
	title: str,
	subtitle: str,
	filters: dict[str, str],
	queue: str,
) -> dict[str, object]:
	if not common.can_read("Supplier Quotation"):
		return _supplier_quotation_payload(queue_key, title, subtitle, filters, [], common.restricted_state(f"{title} restricted", "Supplier Quotation"))

	rows = _supplier_quotation_rows(filters, queue)
	state = common.ready_state() if rows else common.empty_state(
		f"No {title.lower()}",
		"No visible supplier quotations match the current filters.",
	)
	return _supplier_quotation_payload(queue_key, title, subtitle, filters, rows, state)


def _supplier_quotation_rows(filters: dict[str, str], queue: str) -> list[dict[str, object]]:
	records = common.get_list(
		"Supplier Quotation",
		fields=SQ_FIELDS,
		filters=supplier_quotation_filters(filters, queue=queue),
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
					"quotation": {"value": name, "meta": record.get("supplier_name") or record.get("supplier") or ""},
					"company": record.get("company") or "-",
					"date": cstr(record.get("transaction_date") or ""),
					"valid_till": cstr(record.get("valid_till") or ""),
					"status": record.get("status") or "-",
					"total": _money(record.get("grand_total"), record.get("currency")),
				},
				"actions": [{"key": "open_record", "label": "Open"}],
			}
		)
	return rows


def _supplier_quotation_payload(
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
			"chips": [{"label": "Read-only"}],
		},
		"controls": {
			"fields": _supplier_quotation_control_fields(filters),
			"actions": common.standard_actions(),
			"scopeChips": ["Supplier Quotation", "Read-only sourcing"],
		},
		"metrics": [common.metric("Visible quotations", len(rows), "Filtered supplier quotation records.")],
		"results": {
			"title": "Supplier quotation records",
			"meta": f"{len(rows)} shown",
			"columns": [
				{"key": "quotation", "label": "Supplier Quotation"},
				{"key": "company", "label": "Company"},
				{"key": "date", "label": "Date"},
				{"key": "valid_till", "label": "Valid Till"},
				{"key": "status", "label": "Status"},
				{"key": "total", "label": "Total"},
			],
			"rows": rows,
			"rowActions": True,
			"state": state,
		},
		"action_targets": common.action_targets_for_rows("Supplier Quotation", rows),
	}


def _supplier_status_map(rfq_names: list[str]) -> dict[str, dict[str, int]]:
	if not rfq_names or not quote_status_available():
		return {}
	rows = _get_all(
		RFQ_QUOTE_STATUS_DOCTYPE,
		filters={"parent": ["in", rfq_names]},
		fields=RFQ_SUPPLIER_FIELDS,
		order_by="idx asc",
	)
	status_map: dict[str, dict[str, int]] = defaultdict(lambda: {"Pending": 0, "Received": 0})
	for row in rows:
		parent = cstr(row.get("parent")).strip()
		status = cstr(row.get("quote_status")).strip() or "Pending"
		if parent and status in {"Pending", "Received"}:
			status_map[parent][status] += 1
	return dict(status_map)


def _rfq_names_by_quote_status(status: str) -> set[str]:
	if not common.can_read("Request for Quotation") or not quote_status_available():
		return set()
	rows = _get_all(
		RFQ_QUOTE_STATUS_DOCTYPE,
		filters={"quote_status": status},
		fields=["parent", "quote_status"],
		limit=common.ROW_LIMIT * 4,
	)
	return {cstr(row.get("parent")).strip() for row in rows if cstr(row.get("parent")).strip()}


def _partially_quoted_rfq_names() -> set[str]:
	if not common.can_read("Request for Quotation") or not quote_status_available():
		return set()
	rows = _get_all(RFQ_QUOTE_STATUS_DOCTYPE, filters={}, fields=["parent", "quote_status"], limit=common.ROW_LIMIT * 6)
	statuses: dict[str, set[str]] = defaultdict(set)
	for row in rows:
		parent = cstr(row.get("parent")).strip()
		status = cstr(row.get("quote_status")).strip()
		if parent and status:
			statuses[parent].add(status)
	return {parent for parent, values in statuses.items() if "Pending" in values and "Received" in values}


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


def _rfq_control_fields(filters: dict[str, str]) -> list[dict[str, object]]:
	return [
		{"key": "keyword", "label": "Search", "type": "text", "value": filters.get("keyword", ""), "placeholder": "RFQ ID"},
		{"key": "company", "label": "Company", "type": "text", "value": filters.get("company", "")},
		{
			"key": "status",
			"label": "Status",
			"type": "select",
			"value": filters.get("status", ""),
			"options": [
				{"label": "All", "value": ""},
				{"label": "Draft", "value": "Draft"},
				{"label": "Submitted", "value": "Submitted"},
				{"label": "Cancelled", "value": "Cancelled"},
			],
		},
		{"key": "date_start", "label": "From", "type": "date", "value": filters.get("date_start", "")},
		{"key": "date_end", "label": "To", "type": "date", "value": filters.get("date_end", "")},
	]


def _supplier_quotation_control_fields(filters: dict[str, str]) -> list[dict[str, object]]:
	return [
		{"key": "keyword", "label": "Search", "type": "text", "value": filters.get("keyword", ""), "placeholder": "Quotation ID"},
		{"key": "supplier", "label": "Supplier", "type": "text", "value": filters.get("supplier", "")},
		{"key": "company", "label": "Company", "type": "text", "value": filters.get("company", "")},
		{
			"key": "status",
			"label": "Status",
			"type": "select",
			"value": filters.get("status", ""),
			"options": [
				{"label": "All", "value": ""},
				{"label": "Draft", "value": "Draft"},
				{"label": "Submitted", "value": "Submitted"},
				{"label": "Stopped", "value": "Stopped"},
				{"label": "Expired", "value": "Expired"},
				{"label": "Cancelled", "value": "Cancelled"},
			],
		},
		{"key": "date_start", "label": "From", "type": "date", "value": filters.get("date_start", "")},
		{"key": "date_end", "label": "To", "type": "date", "value": filters.get("date_end", "")},
	]


def _money(value: object, currency: object) -> str:
	amount = flt(value)
	code = cstr(currency).strip()
	if code:
		return f"{code} {amount:,.2f}"
	return f"{amount:,.2f}"
