from __future__ import annotations

from frappe.utils import cstr

from . import common


MR_FIELDS = [
	"name",
	"title",
	"material_request_type",
	"company",
	"transaction_date",
	"schedule_date",
	"status",
	"per_ordered",
	"per_received",
	"modified",
]


def purchase_request_base_filters() -> list[list[object]]:
	return [["Material Request", "material_request_type", "=", "Purchase"]]


def purchase_request_filters(filters: dict[str, str] | None = None, source_only: bool = False) -> list[list[object]]:
	applied = filters or {}
	conditions = purchase_request_base_filters()
	material_request = cstr(applied.get("material_request")).strip()
	if material_request:
		conditions.append(["Material Request", "name", "=", material_request])
	keyword = cstr(applied.get("keyword")).strip()
	if keyword:
		conditions.append(["Material Request", "name", "like", f"%{keyword}%"])
	company = cstr(applied.get("company")).strip()
	if company:
		conditions.append(["Material Request", "company", "=", company])
	status = cstr(applied.get("status")).strip()
	if status:
		conditions.append(["Material Request", "status", "=", status])
	date_start = cstr(applied.get("date_start")).strip()
	if date_start:
		conditions.append(["Material Request", "transaction_date", ">=", date_start])
	date_end = cstr(applied.get("date_end")).strip()
	if date_end:
		conditions.append(["Material Request", "transaction_date", "<=", date_end])
	if source_only:
		conditions.extend(
			[
				["Material Request", "docstatus", "=", 1],
				["Material Request", "status", "not in", ["Stopped", "Cancelled", "Ordered", "Received"]],
				["Material Request", "per_ordered", "<", 100],
			]
		)
	return conditions


def count_purchase_requests_to_source() -> int:
	if not common.can_read("Material Request"):
		return 0
	return common.count("Material Request", filters=purchase_request_filters(source_only=True))


def count_purchase_request_directory() -> int:
	if not common.can_read("Material Request"):
		return 0
	return common.count("Material Request", filters=purchase_request_base_filters())


def build_purchase_request_directory(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_purchase_request_payload(
		queue_key="purchase_request_directory",
		title="Purchase Requests",
		subtitle="Purchase Material Requests only, shaped for sourcing review.",
		filters=filters or {},
		source_only=False,
	)


def build_requests_to_source(filters: dict[str, str] | None = None) -> dict[str, object]:
	return _build_purchase_request_payload(
		queue_key="requests_to_source",
		title="Requests To Source",
		subtitle="Submitted purchase requests that are not fully ordered yet.",
		filters=filters or {},
		source_only=True,
	)


def _build_purchase_request_payload(
	queue_key: str,
	title: str,
	subtitle: str,
	filters: dict[str, str],
	source_only: bool,
) -> dict[str, object]:
	if not common.can_read("Material Request"):
		return _purchase_request_payload(queue_key, title, subtitle, filters, [], common.restricted_state(f"{title} restricted", "Material Request"))

	rows = _purchase_request_rows(filters, source_only=source_only)
	state = common.ready_state() if rows else common.empty_state(
		f"No {title.lower()}",
		"No visible purchase requests match the current filters.",
	)
	return _purchase_request_payload(queue_key, title, subtitle, filters, rows, state)


def _purchase_request_rows(filters: dict[str, str], source_only: bool) -> list[dict[str, object]]:
	records = common.get_list(
		"Material Request",
		fields=MR_FIELDS,
		filters=purchase_request_filters(filters, source_only=source_only),
		order_by="transaction_date desc, modified desc",
	)
	rows: list[dict[str, object]] = []
	for record in records:
		name = cstr(record.get("name")).strip()
		if not name:
			continue
		per_ordered = record.get("per_ordered")
		rows.append(
			{
				"key": name,
				"name": name,
				"cells": {
					"request": {"value": name, "meta": record.get("title") or ""},
					"company": record.get("company") or "-",
					"required_by": cstr(record.get("schedule_date") or ""),
					"status": record.get("status") or "-",
					"ordered": f"{per_ordered or 0}%",
				},
				"actions": [{"key": "open_record", "label": "Review Request"}],
			}
		)
	return rows


def _purchase_request_payload(
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
			"chips": [{"label": "Purchase requests only"}],
		},
		"controls": {
			"fields": [
				{"key": "material_request", "label": "Purchase Request", "type": "link", "linkDoctype": "Material Request", "value": filters.get("material_request", ""), "placeholder": "Select purchase request"},
				{"key": "keyword", "label": "Search request text", "type": "text", "value": filters.get("keyword", ""), "placeholder": "Search request text"},
				{
					"key": "status",
					"label": "Status",
					"type": "select",
					"value": filters.get("status", ""),
					"options": [
						{"label": "All", "value": ""},
						{"label": "Submitted", "value": "Submitted"},
						{"label": "Pending", "value": "Pending"},
						{"label": "Partially Ordered", "value": "Partially Ordered"},
						{"label": "Ordered", "value": "Ordered"},
					],
				},
				{"key": "date_start", "label": "Request Date From", "type": "date", "value": filters.get("date_start", "")},
				{"key": "date_end", "label": "Request Date To", "type": "date", "value": filters.get("date_end", "")},
			],
			"actions": common.standard_actions(),
			"scopeChips": ["Material Request", "Purchase only"],
		},
		"metrics": [
			common.metric("Requests in view", len(rows), "Matching purchase requests."),
		],
		"results": {
			"title": "Purchase request records",
			"meta": f"{len(rows)} shown",
			"columns": [
				{"key": "request", "label": "Request"},
				{"key": "company", "label": "Company"},
				{"key": "required_by", "label": "Required By"},
				{"key": "status", "label": "Status"},
				{"key": "ordered", "label": "Ordered"},
			],
			"rows": rows,
			"rowActions": True,
			"state": state,
		},
		"action_targets": common.page_action_targets_for_rows("procurement-console-purchase-request-review", rows, {row["name"]: {"return_queue": queue_key} for row in rows if row.get("name")}),
	}
