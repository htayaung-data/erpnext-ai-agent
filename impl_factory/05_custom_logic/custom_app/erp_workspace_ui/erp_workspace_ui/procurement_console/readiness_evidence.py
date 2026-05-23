from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from . import common


SUPPLIER_KNOWN_TRADING_LABEL = "Known trading record"
SUPPLIER_NEW_REVIEW_LABEL = "New supplier - review needed"
ITEM_EXISTING_BUYING_LABEL = "Existing buying activity"
ITEM_EXISTING_SALES_LABEL = "Existing sales activity"
ITEM_CATALOG_EVIDENCE_LABEL = "Catalog evidence found"
ITEM_NEW_REVIEW_LABEL = "New item - review needed"
REVIEWED_FOR_BUYING_LABEL = "Reviewed for buying"
NEEDS_SUPPLIER_REVIEW_LABEL = "Needs supplier review"


def _clear_frappe_messages() -> None:
	try:
		if hasattr(frappe, "clear_messages"):
			frappe.clear_messages()
	except Exception:
		pass
	local = getattr(frappe, "local", None)
	if local is None:
		return
	try:
		messages = getattr(local, "message_log", None)
		if isinstance(messages, list):
			messages.clear()
	except Exception:
		pass
	try:
		response = getattr(local, "response", None)
		if isinstance(response, dict):
			response.pop("_server_messages", None)
	except Exception:
		pass


def _safe_get_all(
	doctype: str,
	fields: list[str],
	filters: dict[str, object] | list | None = None,
	order_by: str | None = None,
	limit: int = 200,
) -> list[dict[str, Any]]:
	query: dict[str, Any] = {"fields": fields, "filters": filters or {}, "limit_page_length": limit}
	if order_by:
		query["order_by"] = order_by
	try:
		return list(frappe.get_all(doctype, ignore_permissions=True, **query))
	except TypeError:
		try:
			return list(frappe.get_all(doctype, **query))
		except Exception:
			_clear_frappe_messages()
			return []
	except Exception:
		_clear_frappe_messages()
		return []


def _safe_db_value(doctype: str, name: str, fieldname: str | list[str], as_dict: bool = False) -> Any:
	try:
		return frappe.db.get_value(doctype, name, fieldname, as_dict=as_dict)
	except Exception:
		return {} if as_dict else None


def _unique(values: list[str]) -> list[str]:
	output: list[str] = []
	seen: set[str] = set()
	for value in values:
		name = cstr(value).strip()
		if name and name not in seen:
			seen.add(name)
			output.append(name)
	return output


def _rows_by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
	return {cstr(row.get(key)).strip(): dict(row) for row in rows if cstr(row.get(key)).strip()}


def _contact_has_email(contact: str) -> bool:
	contact_name = cstr(contact).strip()
	if not contact_name:
		return False
	row = _safe_db_value("Contact", contact_name, ["name", "email_id"], as_dict=True) or {}
	if cstr(row.get("email_id")).strip():
		return True
	email_rows = _safe_get_all(
		"Contact Email",
		fields=["email_id", "is_primary"],
		filters=[["Contact Email", "parent", "=", contact_name]],
		order_by="is_primary desc, idx asc",
		limit=5,
	)
	return any(cstr(email_row.get("email_id")).strip() for email_row in email_rows)


def supplier_has_linked_contact_email(supplier: str) -> bool:
	supplier_name = cstr(supplier).strip()
	if not supplier_name:
		return False
	links = _safe_get_all(
		"Dynamic Link",
		fields=["parent"],
		filters={"link_doctype": "Supplier", "link_name": supplier_name, "parenttype": "Contact"},
		order_by="idx asc",
		limit=50,
	)
	return any(_contact_has_email(cstr(link.get("parent")).strip()) for link in links)


def _supplier_rows(names: list[str]) -> dict[str, dict[str, Any]]:
	if not names or not common.can_read("Supplier"):
		return {}
	fields = ["name", "supplier_name"]
	if common.has_field("Supplier", "disabled"):
		fields.append("disabled")
	rows = common.get_list("Supplier", fields=fields, filters=[["Supplier", "name", "in", names]], limit=len(names))
	return _rows_by_key(rows, "name")


def supplier_evidence_for_suppliers(suppliers: list[str]) -> dict[str, dict[str, Any]]:
	names = _unique(suppliers)
	if not names:
		return {}
	evidence = {
		name: {
			"supplier": name,
			"disabled": False,
			"has_rfq_history": False,
			"has_supplier_quotation_history": False,
			"has_purchase_order_history": False,
			"has_trading_history": False,
			"has_linked_contact_email": False,
			"inferred_label": SUPPLIER_NEW_REVIEW_LABEL,
			"inferred_tone": "warning",
		}
		for name in names
	}
	for name, row in _supplier_rows(names).items():
		evidence[name]["disabled"] = bool(row.get("disabled"))

	for row in _safe_get_all("Request for Quotation Supplier", ["supplier", "parent"], filters={"supplier": ["in", names]}, limit=max(200, len(names) * 20)):
		supplier = cstr(row.get("supplier")).strip()
		if supplier in evidence:
			evidence[supplier]["has_rfq_history"] = True
	for row in common.get_list("Supplier Quotation", fields=["name", "supplier"], filters=[["Supplier Quotation", "supplier", "in", names], ["Supplier Quotation", "docstatus", "not in", [2]]], limit=max(200, len(names) * 20)):
		supplier = cstr(row.get("supplier")).strip()
		if supplier in evidence:
			evidence[supplier]["has_supplier_quotation_history"] = True
	for row in common.get_list("Purchase Order", fields=["name", "supplier"], filters=[["Purchase Order", "supplier", "in", names], ["Purchase Order", "docstatus", "not in", [2]]], limit=max(200, len(names) * 20)):
		supplier = cstr(row.get("supplier")).strip()
		if supplier in evidence:
			evidence[supplier]["has_purchase_order_history"] = True

	for name in names:
		entry = evidence[name]
		entry["has_trading_history"] = bool(entry["has_rfq_history"] or entry["has_supplier_quotation_history"] or entry["has_purchase_order_history"])
		entry["has_linked_contact_email"] = supplier_has_linked_contact_email(name)
		if entry["has_trading_history"]:
			entry["inferred_label"] = SUPPLIER_KNOWN_TRADING_LABEL
			entry["inferred_tone"] = "neutral"
	return evidence


def supplier_evidence(supplier: str) -> dict[str, Any]:
	name = cstr(supplier).strip()
	return supplier_evidence_for_suppliers([name]).get(name, {}) if name else {}


def _item_rows(names: list[str]) -> dict[str, dict[str, Any]]:
	if not names or not common.can_read("Item"):
		return {}
	fields = ["name", "item_name"]
	for field in ("disabled", "is_purchase_item"):
		if common.has_field("Item", field):
			fields.append(field)
	rows = common.get_list("Item", fields=fields, filters=[["Item", "name", "in", names]], limit=len(names))
	return _rows_by_key(rows, "name")


def item_evidence_for_items(item_codes: list[str]) -> dict[str, dict[str, Any]]:
	names = _unique(item_codes)
	if not names:
		return {}
	evidence = {
		name: {
			"item_code": name,
			"disabled": False,
			"is_purchase_item": True,
			"has_rfq_history": False,
			"has_supplier_quotation_history": False,
			"has_purchase_order_history": False,
			"has_purchase_receipt_history": False,
			"has_purchase_invoice_history": False,
			"has_sales_order_history": False,
			"has_delivery_note_history": False,
			"has_sales_invoice_history": False,
			"has_buying_transaction_history": False,
			"has_sales_history": False,
			"has_transaction_history": False,
			"has_item_supplier": False,
			"has_buying_price": False,
			"has_catalog_evidence": False,
			"has_any_evidence": False,
			"inferred_label": ITEM_NEW_REVIEW_LABEL,
			"inferred_tone": "warning",
		}
		for name in names
	}
	for name, row in _item_rows(names).items():
		evidence[name]["disabled"] = bool(row.get("disabled"))
		if "is_purchase_item" in row:
			evidence[name]["is_purchase_item"] = bool(row.get("is_purchase_item"))

	for doctype, field, flag in (
		("Request for Quotation Item", "item_code", "has_rfq_history"),
		("Supplier Quotation Item", "item_code", "has_supplier_quotation_history"),
		("Purchase Order Item", "item_code", "has_purchase_order_history"),
		("Purchase Receipt Item", "item_code", "has_purchase_receipt_history"),
		("Purchase Invoice Item", "item_code", "has_purchase_invoice_history"),
	):
		for row in _safe_get_all(doctype, [field, "parent"], filters={field: ["in", names]}, limit=max(300, len(names) * 30)):
			item = cstr(row.get(field)).strip()
			if item in evidence:
				evidence[item][flag] = True

	for doctype, field, flag in (
		("Sales Order Item", "item_code", "has_sales_order_history"),
		("Delivery Note Item", "item_code", "has_delivery_note_history"),
		("Sales Invoice Item", "item_code", "has_sales_invoice_history"),
	):
		filters: list = [[doctype, field, "in", names]]
		if common.has_field(doctype, "docstatus"):
			filters.append([doctype, "docstatus", "=", 1])
		for row in _safe_get_all(doctype, [field, "parent"], filters=filters, limit=max(300, len(names) * 30)):
			item = cstr(row.get(field)).strip()
			if item in evidence:
				evidence[item][flag] = True

	for row in _safe_get_all("Item Supplier", ["parent", "supplier"], filters={"parent": ["in", names]}, limit=max(200, len(names) * 20)):
		item = cstr(row.get("parent")).strip()
		if item in evidence:
			evidence[item]["has_item_supplier"] = True
	for name in names:
		if not evidence[name]["has_item_supplier"]:
			fallback = _safe_get_all("Item Supplier", ["parent", "supplier"], filters={"parent": name}, limit=5)
			evidence[name]["has_item_supplier"] = bool(fallback)

	if common.can_read("Item Price"):
		price_filters: list = [["Item Price", "item_code", "in", names]]
		if common.has_field("Item Price", "buying"):
			price_filters.append(["Item Price", "buying", "=", 1])
		for row in _safe_get_all("Item Price", fields=["name", "item_code"], filters=price_filters, limit=max(300, len(names) * 20)):
			item = cstr(row.get("item_code")).strip()
			if item in evidence:
				evidence[item]["has_buying_price"] = True
	else:
		_clear_frappe_messages()

	for name in names:
		entry = evidence[name]
		entry["has_buying_transaction_history"] = bool(
			entry["has_rfq_history"]
			or entry["has_supplier_quotation_history"]
			or entry["has_purchase_order_history"]
			or entry["has_purchase_receipt_history"]
			or entry["has_purchase_invoice_history"]
		)
		entry["has_sales_history"] = bool(entry["has_sales_order_history"] or entry["has_delivery_note_history"] or entry["has_sales_invoice_history"])
		entry["has_transaction_history"] = bool(entry["has_buying_transaction_history"] or entry["has_sales_history"])
		entry["has_catalog_evidence"] = bool(entry["has_item_supplier"] or entry["has_buying_price"])
		entry["has_any_evidence"] = bool(entry["has_transaction_history"] or entry["has_catalog_evidence"])
		if entry["has_buying_transaction_history"]:
			entry["inferred_label"] = ITEM_EXISTING_BUYING_LABEL
			entry["inferred_tone"] = "neutral"
		elif entry["has_sales_history"]:
			entry["inferred_label"] = ITEM_EXISTING_SALES_LABEL
			entry["inferred_tone"] = "neutral"
		elif entry["has_catalog_evidence"]:
			entry["inferred_label"] = ITEM_CATALOG_EVIDENCE_LABEL
			entry["inferred_tone"] = "neutral"
	return evidence


def item_evidence(item_code: str) -> dict[str, Any]:
	name = cstr(item_code).strip()
	return item_evidence_for_items([name]).get(name, {}) if name else {}
