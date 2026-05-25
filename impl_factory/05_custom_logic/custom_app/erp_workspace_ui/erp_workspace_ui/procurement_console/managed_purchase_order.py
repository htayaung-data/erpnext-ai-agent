from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, nowdate

from . import common, readiness, service


DOCTYPE = "Purchase Order"
ITEM_DOCTYPE = "Purchase Order Item"
FORM_ROUTE = "procurement-console-purchase-order-form"
REVIEW_ROUTE = "procurement-console-po-follow-up"
DIRECTORY_QUEUE = "purchase_order_directory"
DEFAULT_NAMING_SERIES = "PUR-ORD-.YYYY.-"

# Phase 5D intentionally implements direct draft Purchase Order entry only.
# Supplier Quotation-to-PO and Material Request-to-PO conversion stay deferred
# because ERPNext native mappers require submitted source documents and carry
# source-reference/default-supplier behavior that must not be custom-copied.

_FORBIDDEN_FRAGMENTS = {
    "submit",
    "approve",
    "reject",
    "cancel",
    "amend",
    "stop",
    "close",
    "hold",
    "resume",
    "receive",
    "receipt",
    "bill",
    "invoice",
    "pay",
    "payment",
    "item_price",
    "default_supplier",
    "set_default_supplier",
    "purchase_receipt",
    "purchase_invoice",
    "create_receipt",
    "create_invoice",
    "get_items_from",
}


def _state(kind: str, title: str, detail: str) -> dict[str, str]:
    return {"kind": kind, "title": title, "detail": detail}


def _restricted(detail: str | None = None) -> dict[str, object]:
    return {
        "state": _state(
            "restricted",
            "Purchase Order form restricted",
            detail or "You do not have permission to use the managed Purchase Order form.",
        )
    }


def _error(title: str, detail: str) -> dict[str, object]:
    return {"state": _state("error", title, detail)}


def _unavailable(title: str, detail: str) -> dict[str, object]:
    return {"state": _state("unavailable", title, detail)}


def _ready(title: str = "Ready") -> dict[str, str]:
    return {"kind": "ready", "title": title, "detail": ""}


def _authenticated_user() -> bool:
    return cstr(getattr(frappe.session, "user", "")).strip() not in {"", "Guest"}


def _has_procurement_form_access() -> bool:
    return _authenticated_user() and service.has_procurement_access()


def _can_create_purchase_order() -> bool:
    return _has_procurement_form_access() and common.can_read(DOCTYPE) and common.can_write(DOCTYPE) and common.can_create(DOCTYPE)


def _can_edit_purchase_order() -> bool:
    return _has_procurement_form_access() and common.can_read(DOCTYPE) and common.can_write(DOCTYPE)


def _document_value(doc: object, fieldname: str, default: Any = None) -> Any:
    if isinstance(doc, dict):
        return doc.get(fieldname, default)
    return getattr(doc, fieldname, default)


def _set_document_value(doc: object, fieldname: str, value: Any) -> None:
    if hasattr(doc, "set"):
        doc.set(fieldname, value)
    else:
        setattr(doc, fieldname, value)


def _default_company() -> str:
    for getter in (
        lambda: frappe.defaults.get_user_default("Company"),
        lambda: frappe.defaults.get_default("company"),
        lambda: frappe.db.get_single_value("Global Defaults", "default_company"),
    ):
        try:
            value = cstr(getter()).strip()
        except Exception:
            value = ""
        if value:
            return value
    try:
        rows = frappe.get_list("Company", fields=["name"], limit_page_length=1)
    except Exception:
        rows = []
    if rows:
        return cstr(rows[0].get("name") if isinstance(rows[0], dict) else getattr(rows[0], "name", "")).strip()
    return ""


def _default_currency(company: str | None = None) -> str:
    company_name = cstr(company or "").strip()

    def valid_currency(value: Any) -> str:
        text = cstr(value).strip()
        if not text or (company_name and text == company_name):
            return ""
        return text

    if company_name:
        try:
            value = valid_currency(frappe.db.get_value("Company", company_name, "default_currency"))
        except Exception:
            value = ""
        if value:
            return value
    for getter in (
        lambda: frappe.defaults.get_default("currency"),
        lambda: frappe.db.get_single_value("Global Defaults", "default_currency"),
    ):
        try:
            value = valid_currency(getter())
        except Exception:
            value = ""
        if value:
            return value
    return "MMK"


def _default_buying_price_list() -> str:
    try:
        return cstr(frappe.db.get_single_value("Buying Settings", "buying_price_list")).strip()
    except Exception:
        return ""


def _parse_payload(payload: str | dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str) and payload.strip():
        parsed = json.loads(payload)
        if isinstance(parsed, dict):
            return parsed
    return {}


def _safe_date(value: Any, fallback: str | None = None) -> str:
    text = cstr(value).strip()
    return text or cstr(fallback).strip() or nowdate()


def _get_purchase_order_doc(name: str):
    try:
        return frappe.get_doc(DOCTYPE, name)
    except Exception:
        return None


def _load_item(item_code: str) -> dict[str, Any] | None:
    if not item_code or not common.can_read("Item"):
        return None
    rows = common.get_list(
        "Item",
        fields=["name", "item_code", "item_name", "stock_uom"],
        filters=[["Item", "name", "=", item_code]],
        limit=1,
    )
    if not rows:
        rows = common.get_list(
            "Item",
            fields=["name", "item_code", "item_name", "stock_uom"],
            filters=[["Item", "item_code", "=", item_code]],
            limit=1,
        )
    return rows[0] if rows else None


def _supplier_exists(supplier: str) -> bool:
    if not supplier or not common.can_read("Supplier"):
        return False
    rows = common.get_list("Supplier", fields=["name", "supplier_name"], filters=[["Supplier", "name", "=", supplier]], limit=1)
    return bool(rows)


def _warehouse_exists(warehouse: str) -> bool:
    if not warehouse:
        return True
    if not common.can_read("Warehouse"):
        return False
    rows = common.get_list("Warehouse", fields=["name"], filters=[["Warehouse", "name", "=", warehouse]], limit=1)
    return bool(rows)


def _line_is_blank(raw: dict[str, Any]) -> bool:
    keys = {"item_code", "qty", "rate", "schedule_date", "line_required_by", "warehouse"}
    return not any(cstr(raw.get(key)).strip() for key in keys)


def _normalize_items(items: list[dict[str, Any]], default_required_by: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(items or [], start=1):
        if not isinstance(raw, dict):
            return [], f"Item line {index} is not valid."
        if _line_is_blank(raw):
            continue
        item_code = cstr(raw.get("item_code")).strip()
        if not item_code:
            return [], f"Item line {index} needs an item."
        qty = flt(raw.get("qty"))
        if qty <= 0:
            return [], f"Item line {index} needs a quantity greater than zero."
        if raw.get("rate") in (None, ""):
            return [], f"Item line {index} needs a rate."
        rate = flt(raw.get("rate"))
        if rate < 0:
            return [], f"Item line {index} needs a rate of zero or greater."
        schedule_date = _safe_date(raw.get("schedule_date") or raw.get("line_required_by"), default_required_by)
        if not schedule_date:
            return [], f"Item line {index} needs a required-by date."
        warehouse = cstr(raw.get("warehouse")).strip()
        if warehouse and not _warehouse_exists(warehouse):
            return [], f"Item line {index} warehouse is not available to this user."
        item = _load_item(item_code)
        if not item:
            return [], f"Item line {index} item is not available to this user."
        stock_uom = cstr(item.get("stock_uom") or item.get("uom")).strip()
        if not stock_uom:
            return [], f"Item line {index} item does not have a stock UOM."
        amount = qty * rate
        row = {
            "item_code": cstr(item.get("name") or item.get("item_code") or item_code).strip(),
            "item_name": cstr(item.get("item_name") or "").strip(),
            "schedule_date": schedule_date,
            "qty": qty,
            "rate": rate,
            "amount": amount,
            "base_rate": rate,
            "base_amount": amount,
            "uom": stock_uom,
            "stock_uom": stock_uom,
            "conversion_factor": 1,
        }
        if warehouse:
            row["warehouse"] = warehouse
        normalized.append(row)
    if not normalized:
        return [], "Add at least one item line before saving a Purchase Order."
    return normalized, None


def _base_actions(name: str | None = None) -> tuple[list[dict[str, object]], dict[str, object]]:
    actions: list[dict[str, object]] = [
        {"key": "back_to_purchase_orders", "label": "Back to Purchase Orders", "category": "navigation"},
        {"key": "reset_unsaved", "label": "Reset unsaved changes"},
        {"key": "save_purchase_order", "label": "Save Purchase Order", "kind": "primary"},
    ]
    targets: dict[str, object] = {"back_to_purchase_orders": {"kind": "worklist", "queue_key": DIRECTORY_QUEUE}}
    if name and _can_edit_purchase_order():
        actions.append({"key": "review_purchase_order", "label": "Review Purchase Order", "category": "navigation"})
        targets["review_purchase_order"] = {"kind": "page", "route": REVIEW_ROUTE, "route_parts": [name]}
    return actions, targets


def _empty_line(default_required_by: str | None = None, warehouse: str | None = None) -> dict[str, Any]:
    return {
        "item_code": "",
        "qty": "",
        "rate": "",
        "schedule_date": cstr(default_required_by or "").strip(),
        "warehouse": cstr(warehouse or "").strip(),
        "uom": "",
        "amount": 0,
    }


def _form_payload(
    name: str | None,
    header: dict[str, Any] | None = None,
    items: list[dict[str, Any]] | None = None,
) -> dict[str, object]:
    saved = bool(name and name != "new")
    header = dict(header or {})
    company = cstr(header.get("company") or _default_company()).strip()
    currency = cstr(header.get("currency") or _default_currency(company)).strip()
    default_required_by = cstr(header.get("schedule_date") or header.get("default_required_by") or "").strip()
    set_warehouse = cstr(header.get("set_warehouse") or "").strip()
    buying_price_list = cstr(header.get("buying_price_list") or _default_buying_price_list()).strip()
    actions, targets = _base_actions(name if saved else None)
    title = name if saved else "New Purchase Order"
    return {
        "state": _ready("Purchase Order form ready"),
        "page": {"title": title, "route": FORM_ROUTE},
        "summary": {
            "layout": "detail_header",
            "kicker": "Purchase Order",
            "title": title,
            "subtitle": "Record supplier order details before operational processing.",
            "chips": [
                {"label": "Purchase Order Recorded" if saved else "New Purchase Order", "tone": "review"},
                {"label": "Buying order", "tone": "neutral"},
            ],
        },
        "form": {
            "name": name or "new",
            "mode": "edit" if saved else "new",
            "doctype": DOCTYPE,
            "header": {
                "supplier": cstr(header.get("supplier") or "").strip(),
                "transaction_date": _safe_date(header.get("transaction_date")),
                "schedule_date": default_required_by,
                "default_required_by": default_required_by,
                "set_warehouse": set_warehouse,
                "buying_price_list": buying_price_list,
                "company": company,
                "currency": currency,
                "conversion_rate": flt(header.get("conversion_rate") or 1) or 1,
            },
            "items": items if items is not None else [_empty_line(default_required_by, set_warehouse)],
        },
        "controls": {"actions": actions, "summaryToolbar": True},
        "action_targets": targets,
        "readiness_context": readiness.get_purchase_order_readiness_context(name) if saved else {},
        "conversion": {
            "supplier_quotation_to_purchase_order": "deferred",
            "material_request_to_purchase_order": "deferred",
        },
    }


def _doc_to_form_payload(doc: object) -> dict[str, object]:
    items = []
    for child in list(_document_value(doc, "items", []) or []):
        qty = flt(_document_value(child, "qty", 0))
        rate = flt(_document_value(child, "rate", 0))
        amount = flt(_document_value(child, "amount", qty * rate))
        items.append(
            {
                "item_code": _document_value(child, "item_code", ""),
                "qty": qty,
                "rate": rate,
                "amount": amount,
                "schedule_date": _document_value(child, "schedule_date", ""),
                "warehouse": _document_value(child, "warehouse", ""),
                "uom": _document_value(child, "uom", _document_value(child, "stock_uom", "")),
            }
        )
    return _form_payload(
        cstr(_document_value(doc, "name", "")).strip(),
        {
            "supplier": _document_value(doc, "supplier", ""),
            "transaction_date": _document_value(doc, "transaction_date", nowdate()),
            "schedule_date": _document_value(doc, "schedule_date", ""),
            "set_warehouse": _document_value(doc, "set_warehouse", ""),
            "buying_price_list": _document_value(doc, "buying_price_list", _default_buying_price_list()),
            "company": _document_value(doc, "company", _default_company()),
            "currency": _document_value(doc, "currency", _default_currency(_document_value(doc, "company", ""))),
            "conversion_rate": _document_value(doc, "conversion_rate", 1),
        },
        items,
    )


@frappe.whitelist()
def get_managed_purchase_order_context(name: str | None = None, mode: str | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read(DOCTYPE):
        return _restricted()
    normalized_name = cstr(name or mode or "new").strip() or "new"
    if normalized_name == "new":
        if not _can_create_purchase_order():
            return _restricted("You need Purchase Order create permission to create an order.")
        return _form_payload(None)

    if not _can_edit_purchase_order():
        return _restricted("You need Purchase Order write permission to edit an order.")
    doc = _get_purchase_order_doc(normalized_name)
    if not doc:
        return _unavailable("Purchase Order unavailable", "This Purchase Order is not available to the managed form.")
    if int(_document_value(doc, "docstatus", 0) or 0) != 0:
        return _restricted("Submitted or cancelled Purchase Orders are read-only in the Procurement review page.")
    return _doc_to_form_payload(doc)


@frappe.whitelist()
def save_managed_purchase_order(payload: str | dict[str, Any] | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read(DOCTYPE) or not common.can_write(DOCTYPE):
        return _restricted()
    try:
        data = _parse_payload(payload)
    except Exception:
        return _error("Purchase Order not saved", "The Purchase Order payload could not be read.")

    header = data.get("header") if isinstance(data.get("header"), dict) else {}
    items = data.get("items") if isinstance(data.get("items"), list) else []
    name = cstr(data.get("name") or header.get("name")).strip()
    if name == "new":
        name = ""

    forbidden = _payload_forbidden_keys(data)
    if forbidden:
        return _error("Purchase Order not saved", "This form can only update approved fields. Remove unsupported fields and try again.")

    if name:
        if not _can_edit_purchase_order():
            return _restricted("You need Purchase Order write permission to update this order.")
        doc = _get_purchase_order_doc(name)
        if not doc:
            return _unavailable("Purchase Order unavailable", "This Purchase Order is not available for editing.")
        if int(_document_value(doc, "docstatus", 0) or 0) != 0:
            return _error("Purchase Order not saved", "Submitted or cancelled Purchase Orders cannot be edited here.")
        if hasattr(doc, "check_permission"):
            doc.check_permission("write")
    else:
        if not _can_create_purchase_order():
            return _restricted("You need Purchase Order create permission to create an order.")
        doc = frappe.get_doc({"doctype": DOCTYPE})
        _set_document_value(doc, "naming_series", DEFAULT_NAMING_SERIES)

    supplier = cstr(header.get("supplier")).strip()
    if not supplier:
        return _error("Purchase Order not saved", "Choose a supplier before saving a Purchase Order.")
    if not _supplier_exists(supplier):
        return _error("Purchase Order not saved", "The selected supplier is not available to this user.")

    company = cstr(header.get("company") or _default_company()).strip()
    if not company:
        return _unavailable("Company unavailable", "A default company is required before saving a Purchase Order.")
    currency = cstr(header.get("currency") or _default_currency(company)).strip()
    if not currency:
        return _unavailable("Currency unavailable", "A default currency is required before saving a Purchase Order.")
    conversion_rate = flt(header.get("conversion_rate") or 1) or 1
    default_required_by = cstr(header.get("schedule_date") or header.get("default_required_by") or "").strip()
    set_warehouse = cstr(header.get("set_warehouse") or "").strip()
    if set_warehouse and not _warehouse_exists(set_warehouse):
        return _error("Purchase Order not saved", "The selected target warehouse is not available to this user.")
    normalized_items, item_error = _normalize_items(items, default_required_by)
    if item_error:
        return _error("Purchase Order not saved", item_error)

    _set_document_value(doc, "supplier", supplier)
    _set_document_value(doc, "transaction_date", _safe_date(header.get("transaction_date")))
    _set_document_value(doc, "schedule_date", default_required_by)
    _set_document_value(doc, "set_warehouse", set_warehouse)
    _set_document_value(doc, "company", company)
    _set_document_value(doc, "currency", currency)
    _set_document_value(doc, "conversion_rate", conversion_rate)
    buying_price_list = cstr(header.get("buying_price_list") or _default_buying_price_list()).strip()
    if buying_price_list:
        _set_document_value(doc, "buying_price_list", buying_price_list)
    if hasattr(doc, "set"):
        doc.set("items", [])
    else:
        setattr(doc, "items", [])
    for row in normalized_items:
        if hasattr(doc, "append"):
            doc.append("items", row)
        else:
            doc.items.append(row)

    try:
        if hasattr(doc, "run_method"):
            for method in ("set_missing_values", "calculate_taxes_and_totals"):
                try:
                    doc.run_method(method)
                except Exception:
                    pass
        if name:
            doc.save()
        else:
            doc.insert()
    except Exception as exc:
        return _error("Purchase Order not saved", cstr(exc) or "ERPNext validation stopped the Purchase Order save.")

    saved_name = cstr(_document_value(doc, "name", name)).strip()
    payload_out = _doc_to_form_payload(doc)
    payload_out["saved"] = True
    payload_out["message"] = f"Purchase Order {saved_name} recorded for operational review."
    payload_out["route"] = f"/desk/{FORM_ROUTE}/{saved_name}"
    payload_out["review_route"] = f"/desk/{REVIEW_ROUTE}/{saved_name}"
    return payload_out


def _payload_forbidden_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = cstr(key).strip().lower()
            if lowered and any(fragment in lowered for fragment in _FORBIDDEN_FRAGMENTS):
                found.add(cstr(key).strip())
            found.update(_payload_forbidden_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_payload_forbidden_keys(child))
    return found


@frappe.whitelist()
def get_managed_purchase_order_item_defaults(item_code: str | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read("Item"):
        return _restricted("You do not have Item read permission for Purchase Order item lookup.")
    item = _load_item(cstr(item_code).strip())
    if not item:
        return _unavailable("Item unavailable", "The selected item is not available to this user.")
    stock_uom = cstr(item.get("stock_uom") or item.get("uom")).strip()
    if not stock_uom:
        return _unavailable("Item UOM unavailable", "The selected item does not have a stock UOM.")
    return {
        "state": _ready("Item defaults ready"),
        "item": {
            "item_code": cstr(item.get("name") or item.get("item_code") or item_code).strip(),
            "item_name": cstr(item.get("item_name") or "").strip(),
            "uom": stock_uom,
            "stock_uom": stock_uom,
            "conversion_factor": 1,
        },
    }
