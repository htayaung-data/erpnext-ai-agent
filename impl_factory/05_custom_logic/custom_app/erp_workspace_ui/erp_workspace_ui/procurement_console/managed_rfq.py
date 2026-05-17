from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, nowdate

from . import common, service


DOCTYPE = "Request for Quotation"
ITEM_DOCTYPE = "Request for Quotation Item"
SUPPLIER_DOCTYPE = "Request for Quotation Supplier"
FORM_ROUTE = "procurement-console-rfq-form"
REVIEW_ROUTE = "procurement-console-rfq-review"
DIRECTORY_QUEUE = "rfq_directory"
DEFAULT_SUBJECT = "Request for Quotation"
DEFAULT_MESSAGE = "Please supply the specified items at the best possible rates"

# Phase 5B intentionally does not implement PR-to-RFQ conversion. ERPNext's
# native material_request.make_request_for_quotation mapping requires submitted
# Material Requests (docstatus = 1), while Phase 5A records internal Purchase
# Requests as drafts. A governed PR submit/review step is required before a
# productized PR-to-RFQ conversion can safely call that native mapper.

_ALLOWED_HEADER_FIELDS = {"name", "transaction_date", "schedule_date", "company", "subject", "message_for_supplier"}
_ALLOWED_SUPPLIER_FIELDS = {"supplier"}
_ALLOWED_ITEM_FIELDS = {"item_code", "qty", "schedule_date", "warehouse"}
_FORBIDDEN_FRAGMENTS = {
    "submit",
    "cancel",
    "amend",
    "stop",
    "close",
    "send",
    "email",
    "portal",
    "supplier_quotation",
    "purchase_order",
    "item_price",
    "default_supplier",
    "create_supplier_quotation",
    "create_purchase_order",
}


def _state(kind: str, title: str, detail: str) -> dict[str, str]:
    return {"kind": kind, "title": title, "detail": detail}


def _restricted(detail: str | None = None) -> dict[str, object]:
    return {
        "state": _state(
            "restricted",
            "RFQ form restricted",
            detail or "You do not have permission to use the managed RFQ form.",
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


def _can_create_rfq() -> bool:
    return _has_procurement_form_access() and common.can_read(DOCTYPE) and common.can_write(DOCTYPE) and common.can_create(DOCTYPE)


def _can_edit_rfq() -> bool:
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


def _get_rfq_doc(name: str):
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


def _normalize_suppliers(suppliers: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str | None]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(suppliers or [], start=1):
        if not isinstance(raw, dict):
            return [], f"Supplier line {index} is not valid."
        supplier = cstr(raw.get("supplier")).strip()
        if not supplier:
            return [], f"Supplier line {index} needs a supplier."
        if supplier in seen:
            return [], f"Supplier {supplier} is already included."
        if not _supplier_exists(supplier):
            return [], f"Supplier line {index} is not available to this user."
        seen.add(supplier)
        normalized.append({"supplier": supplier})
    if not normalized:
        return [], "Add at least one supplier before saving an RFQ."
    return normalized, None


def _normalize_items(items: list[dict[str, Any]], default_schedule_date: str) -> tuple[list[dict[str, Any]], str | None]:
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
        schedule_date = _safe_date(raw.get("schedule_date"), default_schedule_date)
        if not schedule_date:
            return [], f"Item line {index} needs a required-by date."
        item = _load_item(item_code)
        if not item:
            return [], f"Item line {index} item is not available to this user."
        stock_uom = cstr(item.get("stock_uom") or item.get("uom")).strip()
        if not stock_uom:
            return [], f"Item line {index} item does not have a stock UOM."
        warehouse = cstr(raw.get("warehouse")).strip()
        if warehouse and not _warehouse_exists(warehouse):
            return [], f"Item line {index} warehouse is not available to this user."
        row = {
            "item_code": cstr(item.get("name") or item.get("item_code") or item_code).strip(),
            "qty": qty,
            "schedule_date": schedule_date,
            "uom": stock_uom,
            "stock_uom": stock_uom,
            "conversion_factor": 1,
        }
        if warehouse:
            row["warehouse"] = warehouse
        normalized.append(row)
    if not normalized:
        return [], "Add at least one item line before saving an RFQ."
    return normalized, None


def _base_actions(name: str | None = None) -> tuple[list[dict[str, object]], dict[str, object]]:
    actions: list[dict[str, object]] = [
        {"key": "back_to_rfqs", "label": "Back to RFQs", "category": "navigation"},
        {"key": "reset_unsaved", "label": "Reset unsaved changes"},
        {"key": "save_rfq", "label": "Save RFQ", "kind": "primary"},
    ]
    targets: dict[str, object] = {"back_to_rfqs": {"kind": "worklist", "queue_key": DIRECTORY_QUEUE}}
    if name and _can_edit_rfq():
        actions.append({"key": "review_rfq", "label": "Review RFQ", "category": "navigation"})
        targets["review_rfq"] = {"kind": "page", "route": REVIEW_ROUTE, "route_parts": [name]}
    return actions, targets


def _form_payload(
    name: str | None,
    header: dict[str, Any] | None = None,
    suppliers: list[dict[str, Any]] | None = None,
    items: list[dict[str, Any]] | None = None,
) -> dict[str, object]:
    saved = bool(name and name != "new")
    header = dict(header or {})
    transaction_date = _safe_date(header.get("transaction_date"))
    schedule_date = cstr(header.get("schedule_date") or "").strip()
    company = cstr(header.get("company") or _default_company()).strip()
    subject = cstr(header.get("subject") or DEFAULT_SUBJECT).strip() or DEFAULT_SUBJECT
    message = cstr(header.get("message_for_supplier") or DEFAULT_MESSAGE).strip() or DEFAULT_MESSAGE
    actions, targets = _base_actions(name if saved else None)
    title = name if saved else "New RFQ"
    return {
        "state": _ready("RFQ form ready"),
        "page": {"title": title, "route": FORM_ROUTE},
        "summary": {
            "layout": "detail_header",
            "kicker": "Request for Quotation",
            "title": title,
            "subtitle": "Prepare supplier sourcing request before sending.",
            "chips": [
                {"label": "RFQ Recorded" if saved else "New RFQ", "tone": "review"},
                {"label": "Sourcing", "tone": "neutral"},
            ],
        },
        "form": {
            "name": name or "new",
            "mode": "edit" if saved else "new",
            "doctype": DOCTYPE,
            "header": {
                "transaction_date": transaction_date,
                "schedule_date": schedule_date,
                "company": company,
                "subject": subject,
                "message_for_supplier": message,
            },
            "suppliers": suppliers or [],
            "items": items or [],
        },
        "controls": {"actions": actions, "summaryToolbar": True},
        "action_targets": targets,
        "conversion": {
            "purchase_request_to_rfq": "deferred",
            "detail": "PR-to-RFQ conversion is deferred because ERPNext native mapping requires submitted Material Requests. Phase 5A currently records internal Purchase Requests as drafts. A governed PR submit/review step is required before productized PR-to-RFQ conversion.",
        },
    }


def _doc_to_form_payload(doc: object) -> dict[str, object]:
    suppliers = []
    for child in list(_document_value(doc, "suppliers", []) or []):
        suppliers.append({"supplier": _document_value(child, "supplier", "")})
    items = []
    for child in list(_document_value(doc, "items", []) or []):
        items.append(
            {
                "item_code": _document_value(child, "item_code", ""),
                "qty": _document_value(child, "qty", ""),
                "schedule_date": _document_value(child, "schedule_date", ""),
                "warehouse": _document_value(child, "warehouse", ""),
                "uom": _document_value(child, "uom", _document_value(child, "stock_uom", "")),
            }
        )
    return _form_payload(
        cstr(_document_value(doc, "name", "")).strip(),
        {
            "transaction_date": _document_value(doc, "transaction_date", nowdate()),
            "schedule_date": _document_value(doc, "schedule_date", ""),
            "company": _document_value(doc, "company", _default_company()),
            "subject": _document_value(doc, "subject", DEFAULT_SUBJECT),
            "message_for_supplier": _document_value(doc, "message_for_supplier", DEFAULT_MESSAGE),
        },
        suppliers,
        items,
    )


@frappe.whitelist()
def get_managed_rfq_context(name: str | None = None, mode: str | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read(DOCTYPE):
        return _restricted()
    normalized_name = cstr(name or mode or "new").strip() or "new"
    if normalized_name == "new":
        if not _can_create_rfq():
            return _restricted("You need Request for Quotation create permission to create an RFQ.")
        return _form_payload(None)

    if not _can_edit_rfq():
        return _restricted("You need Request for Quotation write permission to edit an RFQ.")
    doc = _get_rfq_doc(normalized_name)
    if not doc:
        return _unavailable("RFQ unavailable", "This RFQ is not available to the managed form.")
    if int(_document_value(doc, "docstatus", 0) or 0) != 0:
        return _restricted("Submitted or cancelled RFQs are read-only in the Procurement review page.")
    return _doc_to_form_payload(doc)


@frappe.whitelist()
def save_managed_rfq_draft(payload: str | dict[str, Any] | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read(DOCTYPE) or not common.can_write(DOCTYPE):
        return _restricted()
    try:
        data = _parse_payload(payload)
    except Exception:
        return _error("RFQ not saved", "The RFQ payload could not be read.")

    header = data.get("header") if isinstance(data.get("header"), dict) else {}
    suppliers = data.get("suppliers") if isinstance(data.get("suppliers"), list) else []
    items = data.get("items") if isinstance(data.get("items"), list) else []
    name = cstr(data.get("name") or header.get("name")).strip()
    if name == "new":
        name = ""

    forbidden = _payload_forbidden_keys(data)
    if forbidden:
        return _error("RFQ not saved", f"This form cannot set {', '.join(sorted(forbidden))}.")

    if name:
        if not _can_edit_rfq():
            return _restricted("You need Request for Quotation write permission to update this RFQ.")
        doc = _get_rfq_doc(name)
        if not doc:
            return _unavailable("RFQ unavailable", "This RFQ is not available for editing.")
        if int(_document_value(doc, "docstatus", 0) or 0) != 0:
            return _error("RFQ not saved", "Submitted or cancelled RFQs cannot be edited here.")
        if hasattr(doc, "check_permission"):
            doc.check_permission("write")
    else:
        if not _can_create_rfq():
            return _restricted("You need Request for Quotation create permission to create an RFQ.")
        doc = frappe.get_doc({"doctype": DOCTYPE})

    transaction_date = _safe_date(header.get("transaction_date"))
    schedule_date = _safe_date(header.get("schedule_date"), transaction_date)
    company = cstr(header.get("company") or _default_company()).strip()
    subject = cstr(header.get("subject") or DEFAULT_SUBJECT).strip() or DEFAULT_SUBJECT
    message = cstr(header.get("message_for_supplier") or DEFAULT_MESSAGE).strip() or DEFAULT_MESSAGE
    normalized_suppliers, supplier_error = _normalize_suppliers(suppliers)
    if supplier_error:
        return _error("RFQ not saved", supplier_error)
    normalized_items, item_error = _normalize_items(items, schedule_date)
    if item_error:
        return _error("RFQ not saved", item_error)
    if not company:
        return _unavailable("Company unavailable", "A default company is required before saving an RFQ.")

    _set_document_value(doc, "transaction_date", transaction_date)
    _set_document_value(doc, "schedule_date", schedule_date)
    _set_document_value(doc, "company", company)
    _set_document_value(doc, "subject", subject)
    _set_document_value(doc, "message_for_supplier", message)
    if hasattr(doc, "set"):
        doc.set("suppliers", [])
        doc.set("items", [])
    else:
        setattr(doc, "suppliers", [])
        setattr(doc, "items", [])
    for row in normalized_suppliers:
        if hasattr(doc, "append"):
            doc.append("suppliers", row)
        else:
            doc.suppliers.append(row)
    for row in normalized_items:
        if hasattr(doc, "append"):
            doc.append("items", row)
        else:
            doc.items.append(row)

    try:
        if name:
            doc.save()
        else:
            doc.insert()
    except Exception as exc:
        return _error("RFQ not saved", cstr(exc) or "ERPNext validation stopped the RFQ save.")

    saved_name = cstr(_document_value(doc, "name", name)).strip()
    payload_out = _doc_to_form_payload(doc)
    payload_out["saved"] = True
    payload_out["message"] = f"RFQ {saved_name} recorded for sourcing review."
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
def get_managed_rfq_item_defaults(item_code: str | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read("Item"):
        return _restricted("You do not have Item read permission for RFQ item lookup.")
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
