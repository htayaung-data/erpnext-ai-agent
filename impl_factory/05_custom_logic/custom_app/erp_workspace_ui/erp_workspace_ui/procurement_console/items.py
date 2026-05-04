from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from . import common, service


ITEM_DETAIL_ROUTE = "procurement-console-item"
ITEM_BASE_FIELDS = ["name", "item_name", "item_group", "stock_uom", "disabled", "modified"]
OPTIONAL_ITEM_FIELDS = ["is_purchase_item", "has_variants"]
ITEM_PRICE_BASE_FIELDS = ["name", "item_code", "price_list", "price_list_rate", "currency", "valid_from", "valid_upto", "uom", "modified"]
OPTIONAL_ITEM_PRICE_FIELDS = ["supplier", "buying"]
ITEM_SUPPLIER_FIELDS = ["name", "parent", "supplier", "supplier_part_no", "modified"]
OPTIONAL_ITEM_SUPPLIER_FIELDS = ["lead_time_days"]
PO_FIELDS = ["name", "supplier", "supplier_name", "transaction_date", "schedule_date", "status", "per_received", "per_billed", "modified"]
SQ_FIELDS = ["name", "supplier", "supplier_name", "transaction_date", "valid_till", "status", "grand_total", "currency", "modified"]


def item_filters(filters: dict[str, str] | None = None) -> list[list[object]]:
	applied = filters or {}
	conditions: list[list[object]] = []
	item = cstr(applied.get("item")).strip()
	if item:
		conditions.append(["Item", "name", "=", item])
	keyword = cstr(applied.get("keyword")).strip()
	if keyword:
		conditions.append(["Item", "item_name", "like", f"%{keyword}%"])
	item_group = cstr(applied.get("item_group")).strip()
	if item_group:
		conditions.append(["Item", "item_group", "=", item_group])
	disabled = cstr(applied.get("disabled")).strip()
	if disabled:
		conditions.append(["Item", "disabled", "=", 1 if disabled == "1" else 0])
	if common.has_field("Item", "is_purchase_item"):
		conditions.append(["Item", "is_purchase_item", "=", 1])
	return conditions


def count_buying_items() -> int:
	if not common.can_read("Item"):
		return 0
	return common.count("Item", filters=item_filters())


def build_buying_item_directory(filters: dict[str, str] | None = None) -> dict[str, object]:
	applied = filters or {}
	if not common.can_read("Item"):
		return _item_directory_payload(
			applied,
			rows=[],
			state=common.restricted_state("Buying Items restricted", "Item"),
			total=0,
		)
	rows = _item_rows(applied)
	state = common.ready_state() if rows else common.empty_state(
		"No buying items found",
		"No visible purchase-enabled items match the current filters.",
	)
	return _item_directory_payload(applied, rows=rows, state=state, total=len(rows))


def _item_rows(filters: dict[str, str]) -> list[dict[str, object]]:
	records = common.get_list(
		"Item",
		fields=_item_fields(),
		filters=item_filters(filters),
		order_by="modified desc",
	)
	rows: list[dict[str, object]] = []
	for record in records:
		name = cstr(record.get("name")).strip()
		if not name:
			continue
		disabled = bool(record.get("disabled"))
		rows.append(
			{
				"key": name,
				"name": name,
				"cells": {
					"item": {"value": record.get("item_name") or name, "meta": name},
					"group": record.get("item_group") or "-",
					"uom": record.get("stock_uom") or "-",
					"status": {"value": "Disabled" if disabled else "Active", "tone": "danger" if disabled else "positive"},
					"modified": cstr(record.get("modified") or ""),
				},
				"actions": [{"key": "open_record", "label": "Open"}],
			}
		)
	return rows


def _item_directory_payload(
	filters: dict[str, str],
	rows: list[dict[str, object]],
	state: dict[str, object],
	total: int,
) -> dict[str, object]:
	return {
		"page": {"title": "Buying Items", "key": "buying_item_directory"},
		"summary": {
			"title": "Buying Items",
			"subtitle": "Purchase-enabled item and catalog context for buyers. Stock operations remain with Warehouse.",
			"chips": [{"label": "Item visibility"}, {"label": "No item or price mutation"}],
		},
		"controls": {
			"fields": [
				{"key": "item", "label": "Item", "type": "link", "linkDoctype": "Item", "value": filters.get("item", "")},
				{"key": "keyword", "label": "Keyword", "type": "text", "value": filters.get("keyword", ""), "placeholder": "Item name contains"},
				{"key": "item_group", "label": "Item Group", "type": "link", "linkDoctype": "Item Group", "value": filters.get("item_group", "")},
				{
					"key": "disabled",
					"label": "Status",
					"type": "select",
					"value": filters.get("disabled", ""),
					"options": [
						{"label": "All", "value": ""},
						{"label": "Active", "value": "0"},
						{"label": "Disabled", "value": "1"},
					],
				},
			],
			"actions": common.standard_actions(),
			"scopeChips": ["Buying item visibility", "Read-only item detail"],
		},
		"metrics": [common.metric("Visible buying items", total, "Filtered purchase-enabled item records.")],
		"results": {
			"title": "Buying item records",
			"meta": f"{total} shown",
			"columns": [
				{"key": "item", "label": "Item"},
				{"key": "group", "label": "Item Group"},
				{"key": "uom", "label": "Stock UOM"},
				{"key": "status", "label": "Status"},
				{"key": "modified", "label": "Modified"},
			],
			"rows": rows,
			"rowActions": True,
			"state": state,
		},
		"action_targets": common.page_action_targets_for_rows(ITEM_DETAIL_ROUTE, rows),
	}


@frappe.whitelist()
def get_item_detail_context(item: str | None = None, name: str | None = None) -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	item_code = cstr(item or name).strip()
	if not service.has_procurement_access(context):
		return _state_payload(item_code, service.restricted_state(), context)
	if not item_code:
		return _state_payload(item_code, common.unavailable_state("Item required", "Open a buying item row to view this page."), context)
	if not common.can_read("Item"):
		return _state_payload(item_code, common.restricted_state("Buying item restricted", "Item"), context)

	record = _get_item(item_code)
	if not record:
		return _state_payload(item_code, common.unavailable_state("Item not found", "The requested item is not visible for this user."), context)

	return _detail_payload(
		record,
		context,
		item_suppliers=_item_suppliers(item_code),
		item_prices=_item_prices(item_code),
		supplier_quotations=_supplier_quotations(item_code),
		purchase_orders=_purchase_orders(item_code),
	)


def _state_payload(item_code: str, state: dict[str, object], context: dict[str, object]) -> dict[str, object]:
	title = item_code or "Buying Item Detail"
	return {
		"page": {"title": "Buying Item Detail", "key": "buying_item_detail", "item": item_code},
		"summary": {
			"kicker": "Procurement item",
			"title": title,
			"subtitle": state["detail"],
			"chips": [{"label": state["kind"], "tone": "blocker" if state["kind"] in {"restricted", "error"} else "neutral"}],
			"facts": [],
		},
		"controls": {"actions": _base_actions()},
		"detail": {
			"state": state,
			"item_suppliers": _empty_table(),
			"item_prices": _empty_table(),
			"supplier_quotations": _empty_table(),
			"purchase_orders": _empty_table(),
		},
		"action_targets": _base_action_targets(),
		"context": {"role_variant": context.get("role_variant")},
	}


def _detail_payload(
	record: dict[str, object],
	context: dict[str, object],
	item_suppliers: list[dict[str, object]],
	item_prices: list[dict[str, object]],
	supplier_quotations: list[dict[str, object]],
	purchase_orders: list[dict[str, object]],
) -> dict[str, object]:
	name = cstr(record.get("name"))
	disabled = bool(record.get("disabled"))
	actions = _base_actions()
	action_targets = _base_action_targets()
	if _can_open_native_item(context):
		actions.append(
			{
				"key": "open_item_form",
				"title": "Open ERP Item Form",
				"label": "Open ERP Item Form",
				"variant": "secondary",
				"category": "governed_native",
				"note": "Uses ERPNext item master permissions.",
			}
		)
		action_targets["open_item_form"] = {
			"kind": "form",
			"doctype": "Item",
			"name": name,
			"native_chrome": common.native_form_context("Item", name=name, leaf_label="ERP Item Form"),
		}

	return {
		"page": {"title": "Buying Item Detail", "key": "buying_item_detail", "item": name},
		"summary": {
			"kicker": "Buying item profile",
			"title": record.get("item_name") or name,
			"subtitle": "Read-only procurement view of supplier, price, quotation, and order context.",
			"chips": [
				{"label": "Disabled" if disabled else "Active", "tone": "danger" if disabled else "good"},
				{"label": "Read-only", "tone": "good"},
			],
			"facts": [
				{"label": "Item Code", "value": name, "meta": cstr(record.get("item_group") or "")},
				{"label": "UOM", "value": record.get("stock_uom") or "--", "meta": "Stock unit"},
				{"label": "Suppliers", "value": len(item_suppliers), "meta": "Visible approved supplier rows"},
				{"label": "Recent Prices", "value": len(item_prices), "meta": "Read-only Item Price rows"},
			],
		},
		"controls": {"actions": actions},
		"detail": {
			"state": common.ready_state(),
			"item": {
				"name": name,
				"item_name": record.get("item_name") or name,
				"item_group": record.get("item_group") or "",
				"stock_uom": record.get("stock_uom") or "",
				"status": "Disabled" if disabled else "Active",
			},
			"item_suppliers": _item_supplier_table(item_suppliers),
			"item_prices": _item_price_table(item_prices),
			"supplier_quotations": _supplier_quotation_table(supplier_quotations),
			"purchase_orders": _purchase_order_table(purchase_orders),
		},
		"action_targets": action_targets,
		"context": {"role_variant": context.get("role_variant")},
	}


def _get_item(item_code: str) -> dict[str, object] | None:
	rows = common.get_list("Item", fields=_item_fields(), filters=[["Item", "name", "=", item_code]], order_by="modified desc", limit=1)
	return dict(rows[0]) if rows else None


def _item_suppliers(item_code: str) -> list[dict[str, object]]:
	return _get_all(
		"Item Supplier",
		filters={"parent": item_code},
		fields=_available_fields("Item Supplier", ITEM_SUPPLIER_FIELDS + OPTIONAL_ITEM_SUPPLIER_FIELDS),
		order_by="modified desc",
	)


def _item_prices(item_code: str) -> list[dict[str, object]]:
	if not common.can_read("Item Price"):
		return []
	filters: list[list[object]] = [["Item Price", "item_code", "=", item_code]]
	if common.has_field("Item Price", "buying"):
		filters.append(["Item Price", "buying", "=", 1])
	return common.get_list(
		"Item Price",
		fields=_available_fields("Item Price", ITEM_PRICE_BASE_FIELDS + OPTIONAL_ITEM_PRICE_FIELDS),
		filters=filters,
		order_by="valid_from desc, modified desc",
		limit=12,
	)


def _supplier_quotations(item_code: str) -> list[dict[str, object]]:
	if not common.can_read("Supplier Quotation"):
		return []
	item_rows = _get_all("Supplier Quotation Item", filters={"item_code": item_code}, fields=["parent", "item_code"], order_by="modified desc")
	parent_names = [cstr(row.get("parent")).strip() for row in item_rows if cstr(row.get("parent")).strip()]
	if not parent_names:
		return []
	return common.get_list(
		"Supplier Quotation",
		fields=SQ_FIELDS,
		filters=[["Supplier Quotation", "name", "in", parent_names]],
		order_by="transaction_date desc, modified desc",
		limit=12,
	)


def _purchase_orders(item_code: str) -> list[dict[str, object]]:
	if not common.can_read("Purchase Order"):
		return []
	item_rows = _get_all("Purchase Order Item", filters={"item_code": item_code}, fields=["parent", "item_code"], order_by="modified desc")
	parent_names = [cstr(row.get("parent")).strip() for row in item_rows if cstr(row.get("parent")).strip()]
	if not parent_names:
		return []
	return common.get_list(
		"Purchase Order",
		fields=PO_FIELDS,
		filters=[["Purchase Order", "name", "in", parent_names]],
		order_by="transaction_date desc, modified desc",
		limit=12,
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


def _item_fields() -> list[str]:
	return _available_fields("Item", ITEM_BASE_FIELDS + OPTIONAL_ITEM_FIELDS)


def _available_fields(doctype: str, fields: list[str]) -> list[str]:
	output = []
	for field in fields:
		if field == "name" or common.has_field(doctype, field):
			output.append(field)
	return output or ["name"]


def _base_actions() -> list[dict[str, object]]:
	return [
		{"key": "back_to_items", "title": "Back to items", "label": "Back to items", "variant": "secondary", "category": "navigation"},
		{"key": "refresh", "title": "Refresh", "label": "Refresh", "variant": "secondary"},
	]


def _base_action_targets() -> dict[str, object]:
	return {"back_to_items": {"kind": "worklist", "queue_key": "buying_item_directory"}}


def _can_open_native_item(context: dict[str, object]) -> bool:
	roles = set(context.get("roles") or [])
	return bool(roles.intersection({"Purchase Master Manager", "Item Manager", "Stock Manager", "System Manager"})) and common.can_write("Item")


def _empty_table() -> dict[str, object]:
	return {"columns": [], "rows": [], "state": common.empty_state()}


def _item_supplier_table(rows: list[dict[str, object]]) -> dict[str, object]:
	return _table(
		"Approved suppliers",
		[
			{"key": "supplier", "label": "Supplier"},
			{"key": "supplier_part_no", "label": "Supplier Part No"},
			{"key": "lead_time", "label": "Lead Time"},
		],
		[
			{
				"key": cstr(row.get("name") or row.get("supplier")),
				"cells": {
					"supplier": row.get("supplier") or "-",
					"supplier_part_no": row.get("supplier_part_no") or "-",
					"lead_time": _days(row.get("lead_time_days")),
				},
			}
			for row in rows
		],
		"No visible approved suppliers",
		"No visible Item Supplier rows are linked to this item.",
	)


def _item_price_table(rows: list[dict[str, object]]) -> dict[str, object]:
	return _table(
		"Supplier price review",
		[
			{"key": "price_list", "label": "Price List"},
			{"key": "supplier", "label": "Supplier"},
			{"key": "rate", "label": "Rate"},
			{"key": "validity", "label": "Validity"},
		],
		[
			{
				"key": cstr(row.get("name")),
				"cells": {
					"price_list": row.get("price_list") or "-",
					"supplier": row.get("supplier") or "-",
					"rate": _money(row.get("price_list_rate"), row.get("currency")),
					"validity": _validity(row.get("valid_from"), row.get("valid_upto")),
				},
			}
			for row in rows
		],
		"No visible buying prices",
		"No visible buying Item Price rows are linked to this item.",
	)


def _supplier_quotation_table(rows: list[dict[str, object]]) -> dict[str, object]:
	return _table(
		"Recent supplier quotations",
		[
			{"key": "quotation", "label": "Supplier Quotation"},
			{"key": "supplier", "label": "Supplier"},
			{"key": "status", "label": "Status"},
			{"key": "valid_till", "label": "Valid Till"},
			{"key": "total", "label": "Total"},
		],
		[
			{
				"key": cstr(row.get("name")),
				"cells": {
					"quotation": row.get("name") or "-",
					"supplier": row.get("supplier_name") or row.get("supplier") or "-",
					"status": row.get("status") or "-",
					"valid_till": cstr(row.get("valid_till") or ""),
					"total": _money(row.get("grand_total"), row.get("currency")),
				},
			}
			for row in rows
		],
		"No visible supplier quotations",
		"No visible Supplier Quotations are linked to this item.",
	)


def _purchase_order_table(rows: list[dict[str, object]]) -> dict[str, object]:
	return _table(
		"Open purchase orders",
		[
			{"key": "purchase_order", "label": "Purchase Order"},
			{"key": "supplier", "label": "Supplier"},
			{"key": "required_by", "label": "Required By"},
			{"key": "status", "label": "Status"},
			{"key": "received", "label": "Received"},
			{"key": "billed", "label": "Billed"},
		],
		[
			{
				"key": cstr(row.get("name")),
				"cells": {
					"purchase_order": row.get("name") or "-",
					"supplier": row.get("supplier_name") or row.get("supplier") or "-",
					"required_by": cstr(row.get("schedule_date") or ""),
					"status": row.get("status") or "-",
					"received": _percent(row.get("per_received")),
					"billed": _percent(row.get("per_billed")),
				},
			}
			for row in rows
		],
		"No visible purchase orders",
		"No visible Purchase Orders are linked to this item.",
	)


def _table(title: str, columns: list[dict[str, object]], rows: list[dict[str, object]], empty_title: str, empty_detail: str) -> dict[str, object]:
	return {
		"title": title,
		"columns": columns,
		"rows": rows,
		"state": common.ready_state() if rows else common.empty_state(empty_title, empty_detail),
	}


def _days(value: object) -> str:
	if value in (None, ""):
		return "-"
	return f"{flt(value):.0f} days"


def _validity(from_date: object, to_date: object) -> str:
	start = cstr(from_date).strip()
	end = cstr(to_date).strip()
	if start and end:
		return f"{start} to {end}"
	if end:
		return f"Until {end}"
	if start:
		return f"From {start}"
	return "-"


def _percent(value: object) -> str:
	return f"{flt(value):.0f}%"


def _money(value: object, currency: object) -> str:
	amount = flt(value)
	currency_label = cstr(currency).strip()
	amount_text = f"{int(amount):,}" if amount.is_integer() else f"{amount:,.2f}"
	return f"{amount_text} {currency_label}".strip()
