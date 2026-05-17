from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, nowdate

from . import common, service


DOCTYPE = "Supplier Quotation"
ITEM_DOCTYPE = "Supplier Quotation Item"
FORM_ROUTE = "procurement-console-supplier-quotation-form"
REVIEW_ROUTE = "procurement-console-supplier-quotation-review"
DIRECTORY_QUEUE = "supplier_quotation_directory"

# Phase 5C intentionally starts with direct draft Supplier Quotation entry only.
# RFQ-to-Supplier Quotation conversion is deferred because ERPNext's native
# request_for_quotation.make_supplier_quotation_from_rfq mapper requires
# submitted RFQs (docstatus = 1). Supplier Quotation-to-PO conversion is also
# deferred and must use ERPNext's native make_purchase_order mapper when approved.

_FORBIDDEN_FRAGMENTS = {
    "submit",
    "cancel",
    "amend",
    "stop",
    "close",
    "send",
    "email",
    "portal",
    "purchase_order",
    "item_price",
    "default_supplier",
    "create_purchase_order",
    "update_item_price",
    "set_default_supplier",
}


def _state(kind: str, title: str, detail: str) -> dict[str, str]:
    return {"kind": kind, "title": title, "detail": detail}


def _restricted(detail: str | None = None) -> dict[str, object]:
    return {
        "state": _state(
            "restricted",
            "Supplier Quotation form restricted",
            detail or "You do not have permission to use the managed Supplier Quotation form.",
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


def _can_create_supplier_quotation() -> bool:
    return (
        _has_procurement_form_access()
        and common.can_read(DOCTYPE)
        and common.can_write(DOCTYPE)
        and common.can_create(DOCTYPE)
    )


def _can_edit_supplier_quotation() -> bool:
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


def _get_supplier_quotation_doc(name: str):
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


def _normalize_items(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str | None]:
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(items or [], start=1):
        if not isinstance(raw, dict):
            return [], f"Item line {index} is not valid."
        item_code = cstr(raw.get("item_code")).strip()
        if not item_code:
            return [], f"Item line {index} needs an item."
        qty = flt(raw.get("qty"))
        if qty <= 0:
            return [], f"Item line {index} needs a quantity greater than zero."
        rate = flt(raw.get("rate"))
        if rate <= 0:
            return [], f"Item line {index} needs a rate greater than zero."
        item = _load_item(item_code)
        if not item:
            return [], f"Item line {index} item is not available to this user."
        stock_uom = cstr(item.get("stock_uom") or item.get("uom")).strip()
        if not stock_uom:
            return [], f"Item line {index} item does not have a stock UOM."
        amount = qty * rate
        normalized.append(
            {
                "item_code": cstr(item.get("name") or item.get("item_code") or item_code).strip(),
                "qty": qty,
                "rate": rate,
                "amount": amount,
                "base_rate": rate,
                "base_amount": amount,
                "uom": stock_uom,
                "stock_uom": stock_uom,
                "conversion_factor": 1,
            }
        )
    if not normalized:
        return [], "Add at least one item line before saving a Supplier Quotation."
    return normalized, None


def _base_actions(name: str | None = None) -> tuple[list[dict[str, object]], dict[str, object]]:
    actions: list[dict[str, object]] = [
        {"key": "back_to_supplier_quotations", "label": "Back to Supplier Quotations", "category": "navigation"},
        {"key": "reset_unsaved", "label": "Reset unsaved changes"},
        {"key": "save_supplier_quotation", "label": "Save Quotation", "kind": "primary"},
    ]
    targets: dict[str, object] = {"back_to_supplier_quotations": {"kind": "worklist", "queue_key": DIRECTORY_QUEUE}}
    if name and _can_edit_supplier_quotation():
        actions.append({"key": "review_quotation", "label": "Review Quotation", "category": "navigation"})
        targets["review_quotation"] = {"kind": "page", "route": REVIEW_ROUTE, "route_parts": [name]}
    return actions, targets


def _form_payload(
    name: str | None,
    header: dict[str, Any] | None = None,
    items: list[dict[str, Any]] | None = None,
) -> dict[str, object]:
    saved = bool(name and name != "new")
    header = dict(header or {})
    company = cstr(header.get("company") or _default_company()).strip()
    currency = cstr(header.get("currency") or _default_currency(company)).strip()
    actions, targets = _base_actions(name if saved else None)
    title = name if saved else "New Supplier Quotation"
    return {
        "state": _ready("Supplier Quotation form ready"),
        "page": {"title": title, "route": FORM_ROUTE},
        "summary": {
            "layout": "detail_header",
            "kicker": "Supplier Quotation",
            "title": title,
            "subtitle": "Record supplier offer details for buyer comparison.",
            "chips": [
                {"label": "Quotation Recorded" if saved else "New Quotation", "tone": "review"},
                {"label": "Buying offer", "tone": "neutral"},
            ],
        },
        "form": {
            "name": name or "new",
            "mode": "edit" if saved else "new",
            "doctype": DOCTYPE,
            "header": {
                "supplier": cstr(header.get("supplier") or "").strip(),
                "transaction_date": _safe_date(header.get("transaction_date")),
                "valid_till": cstr(header.get("valid_till") or "").strip(),
                "company": company,
                "currency": currency,
                "conversion_rate": flt(header.get("conversion_rate") or 1) or 1,
            },
            "items": items or [],
        },
        "controls": {"actions": actions, "summaryToolbar": True},
        "action_targets": targets,
        "conversion": {
            "rfq_to_supplier_quotation": "deferred",
            "supplier_quotation_to_purchase_order": "deferred",
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
                "uom": _document_value(child, "uom", _document_value(child, "stock_uom", "")),
            }
        )
    return _form_payload(
        cstr(_document_value(doc, "name", "")).strip(),
        {
            "supplier": _document_value(doc, "supplier", ""),
            "transaction_date": _document_value(doc, "transaction_date", nowdate()),
            "valid_till": _document_value(doc, "valid_till", ""),
            "company": _document_value(doc, "company", _default_company()),
            "currency": _document_value(doc, "currency", _default_currency(_document_value(doc, "company", ""))),
            "conversion_rate": _document_value(doc, "conversion_rate", 1),
        },
        items,
    )


@frappe.whitelist()
def get_managed_supplier_quotation_context(name: str | None = None, mode: str | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read(DOCTYPE):
        return _restricted()
    normalized_name = cstr(name or mode or "new").strip() or "new"
    if normalized_name == "new":
        if not _can_create_supplier_quotation():
            return _restricted("You need Supplier Quotation create permission to create a quotation.")
        return _form_payload(None)

    if not _can_edit_supplier_quotation():
        return _restricted("You need Supplier Quotation write permission to edit a quotation.")
    doc = _get_supplier_quotation_doc(normalized_name)
    if not doc:
        return _unavailable("Supplier Quotation unavailable", "This Supplier Quotation is not available to the managed form.")
    if int(_document_value(doc, "docstatus", 0) or 0) != 0:
        return _restricted("Submitted or cancelled Supplier Quotations are read-only in the Procurement review page.")
    return _doc_to_form_payload(doc)


@frappe.whitelist()
def save_managed_supplier_quotation_draft(payload: str | dict[str, Any] | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read(DOCTYPE) or not common.can_write(DOCTYPE):
        return _restricted()
    try:
        data = _parse_payload(payload)
    except Exception:
        return _error("Supplier Quotation not saved", "The Supplier Quotation payload could not be read.")

    header = data.get("header") if isinstance(data.get("header"), dict) else {}
    items = data.get("items") if isinstance(data.get("items"), list) else []
    name = cstr(data.get("name") or header.get("name")).strip()
    if name == "new":
        name = ""

    forbidden = _payload_forbidden_keys(data)
    if forbidden:
        return _error("Supplier Quotation not saved", f"This form cannot set {', '.join(sorted(forbidden))}.")

    if name:
        if not _can_edit_supplier_quotation():
            return _restricted("You need Supplier Quotation write permission to update this quotation.")
        doc = _get_supplier_quotation_doc(name)
        if not doc:
            return _unavailable("Supplier Quotation unavailable", "This Supplier Quotation is not available for editing.")
        if int(_document_value(doc, "docstatus", 0) or 0) != 0:
            return _error("Supplier Quotation not saved", "Submitted or cancelled Supplier Quotations cannot be edited here.")
        if hasattr(doc, "check_permission"):
            doc.check_permission("write")
    else:
        if not _can_create_supplier_quotation():
            return _restricted("You need Supplier Quotation create permission to create a quotation.")
        doc = frappe.get_doc({"doctype": DOCTYPE})

    supplier = cstr(header.get("supplier")).strip()
    if not supplier:
        return _error("Supplier Quotation not saved", "Choose a supplier before saving a quotation.")
    if not _supplier_exists(supplier):
        return _error("Supplier Quotation not saved", "The selected supplier is not available to this user.")

    company = cstr(header.get("company") or _default_company()).strip()
    if not company:
        return _unavailable("Company unavailable", "A default company is required before saving a Supplier Quotation.")
    currency = cstr(header.get("currency") or _default_currency(company)).strip()
    if not currency:
        return _unavailable("Currency unavailable", "A default currency is required before saving a Supplier Quotation.")
    conversion_rate = flt(header.get("conversion_rate") or 1) or 1
    normalized_items, item_error = _normalize_items(items)
    if item_error:
        return _error("Supplier Quotation not saved", item_error)

    _set_document_value(doc, "supplier", supplier)
    _set_document_value(doc, "transaction_date", _safe_date(header.get("transaction_date")))
    _set_document_value(doc, "valid_till", cstr(header.get("valid_till") or "").strip())
    _set_document_value(doc, "company", company)
    _set_document_value(doc, "currency", currency)
    _set_document_value(doc, "conversion_rate", conversion_rate)
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
            try:
                doc.run_method("set_missing_values")
            except Exception:
                pass
        if name:
            doc.save()
        else:
            doc.insert()
    except Exception as exc:
        return _error("Supplier Quotation not saved", cstr(exc) or "ERPNext validation stopped the Supplier Quotation save.")

    saved_name = cstr(_document_value(doc, "name", name)).strip()
    payload_out = _doc_to_form_payload(doc)
    payload_out["saved"] = True
    payload_out["message"] = f"Quotation {saved_name} recorded for buyer comparison."
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
def get_managed_supplier_quotation_item_defaults(item_code: str | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read("Item"):
        return _restricted("You do not have Item read permission for Supplier Quotation item lookup.")
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
