from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, flt, nowdate

from . import common, service


DOCTYPE = "Material Request"
ITEM_DOCTYPE = "Material Request Item"
PURCHASE_TYPE = "Purchase"
FORM_ROUTE = "procurement-console-purchase-request-form"
REVIEW_ROUTE = "procurement-console-purchase-request-review"
DIRECTORY_QUEUE = "purchase_request_directory"

_ALLOWED_HEADER_FIELDS = {"name", "transaction_date", "schedule_date", "company", "material_request_type"}
_ALLOWED_ITEM_FIELDS = {"item_code", "qty", "schedule_date", "warehouse"}
_FORBIDDEN_FRAGMENTS = {
    "submit",
    "cancel",
    "amend",
    "stop",
    "close",
    "receive",
    "bill",
    "pay",
    "item_price",
    "default_supplier",
    "purchase_order",
    "supplier_quotation",
    "request_for_quotation",
}


def _state(kind: str, title: str, detail: str) -> dict[str, str]:
    return {"kind": kind, "title": title, "detail": detail}


def _restricted(detail: str | None = None) -> dict[str, object]:
    return {
        "state": _state(
            "restricted",
            "Purchase Request form restricted",
            detail or "You do not have permission to use the managed Purchase Request form.",
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


def _can_create_purchase_request() -> bool:
    return _has_procurement_form_access() and common.can_read(DOCTYPE) and common.can_write(DOCTYPE) and common.can_create(DOCTYPE)


def _can_edit_purchase_request() -> bool:
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


def _get_purchase_request_doc(name: str):
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


def _warehouse_exists(warehouse: str) -> bool:
    if not warehouse:
        return True
    if not common.can_read("Warehouse"):
        return False
    rows = common.get_list("Warehouse", fields=["name"], filters=[["Warehouse", "name", "=", warehouse]], limit=1)
    return bool(rows)


def _normalize_items(items: list[dict[str, Any]], default_schedule_date: str) -> tuple[list[dict[str, Any]], str | None]:
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(items or [], start=1):
        if not isinstance(raw, dict):
            return [], f"Line {index} is not valid."
        item_code = cstr(raw.get("item_code")).strip()
        if not item_code:
            return [], f"Line {index} needs an item."
        qty = flt(raw.get("qty"))
        if qty <= 0:
            return [], f"Line {index} needs a quantity greater than zero."
        schedule_date = _safe_date(raw.get("schedule_date"), default_schedule_date)
        if not schedule_date:
            return [], f"Line {index} needs a required-by date."
        item = _load_item(item_code)
        if not item:
            return [], f"Line {index} item is not available to this user."
        stock_uom = cstr(item.get("stock_uom") or item.get("uom")).strip()
        if not stock_uom:
            return [], f"Line {index} item does not have a stock UOM."
        warehouse = cstr(raw.get("warehouse")).strip()
        if warehouse and not _warehouse_exists(warehouse):
            return [], f"Line {index} warehouse is not available to this user."
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
        return [], "Add at least one item line before saving a draft."
    return normalized, None


def _base_actions(name: str | None = None) -> tuple[list[dict[str, object]], dict[str, object]]:
    actions: list[dict[str, object]] = [
        {"key": "back_to_purchase_requests", "label": "Back to Purchase Requests", "category": "navigation"},
        {"key": "reset_unsaved", "label": "Reset unsaved changes"},
        {"key": "save_draft", "label": "Save Draft", "kind": "primary"},
    ]
    targets: dict[str, object] = {
        "back_to_purchase_requests": {"kind": "worklist", "queue_key": DIRECTORY_QUEUE},
    }
    if name and _can_edit_purchase_request():
        actions.append({"key": "open_erp_form", "label": "Open ERP Form", "category": "navigation"})
        actions.append({"key": "review_request", "label": "Review Request", "category": "navigation"})
        targets["open_erp_form"] = {
            "kind": "form",
            "doctype": DOCTYPE,
            "name": name,
            "native_chrome": common.native_form_context(DOCTYPE, name=name, leaf_label=name),
        }
        targets["review_request"] = {"kind": "page", "route": REVIEW_ROUTE, "route_parts": [name]}
    return actions, targets


def _form_payload(name: str | None, header: dict[str, Any] | None = None, items: list[dict[str, Any]] | None = None) -> dict[str, object]:
    saved = bool(name and name != "new")
    header = dict(header or {})
    transaction_date = _safe_date(header.get("transaction_date"))
    schedule_date = cstr(header.get("schedule_date") or "").strip()
    company = cstr(header.get("company") or _default_company()).strip()
    actions, targets = _base_actions(name if saved else None)
    title = name if saved else "New Purchase Request"
    return {
        "state": _ready("Purchase Request form ready"),
        "page": {"title": title, "route": FORM_ROUTE},
        "summary": {
            "layout": "detail_header",
            "kicker": "Purchase Request",
            "title": title,
            "subtitle": "Create a draft material request for buyer review.",
            "chips": [
                {"label": "Saved Draft" if saved else "Draft", "tone": "review"},
                {"label": "Purchase only", "tone": "neutral"},
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
                "material_request_type": PURCHASE_TYPE,
            },
            "items": items or [],
        },
        "controls": {"actions": actions, "summaryToolbar": True},
        "action_targets": targets,
    }


def _doc_to_form_payload(doc: object) -> dict[str, object]:
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
        },
        items,
    )


@frappe.whitelist()
def get_managed_purchase_request_context(name: str | None = None, mode: str | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read(DOCTYPE):
        return _restricted()
    normalized_name = cstr(name or mode or "new").strip() or "new"
    if normalized_name == "new":
        if not _can_create_purchase_request():
            return _restricted("You need Material Request create permission to create a Purchase Request draft.")
        return _form_payload(None)

    if not _can_edit_purchase_request():
        return _restricted("You need Material Request write permission to edit a draft Purchase Request.")
    doc = _get_purchase_request_doc(normalized_name)
    if not doc:
        return _unavailable("Purchase Request unavailable", "This Purchase Request is not available to the managed form.")
    if cstr(_document_value(doc, "material_request_type")).strip() != PURCHASE_TYPE:
        return _restricted("Only Purchase Material Requests can be opened in this managed form.")
    if int(_document_value(doc, "docstatus", 0) or 0) != 0:
        return _restricted("Submitted or cancelled Purchase Requests are read-only in the Procurement review page.")
    return _doc_to_form_payload(doc)


@frappe.whitelist()
def save_managed_purchase_request_draft(payload: str | dict[str, Any] | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read(DOCTYPE) or not common.can_write(DOCTYPE):
        return _restricted()
    try:
        data = _parse_payload(payload)
    except Exception:
        return _error("Purchase Request draft not saved", "The draft payload could not be read.")

    header = data.get("header") if isinstance(data.get("header"), dict) else {}
    items = data.get("items") if isinstance(data.get("items"), list) else []
    name = cstr(data.get("name") or header.get("name")).strip()
    if name == "new":
        name = ""

    requested_type = cstr(header.get("material_request_type") or data.get("material_request_type") or PURCHASE_TYPE).strip()
    if requested_type and requested_type != PURCHASE_TYPE:
        return _error("Purchase Request draft not saved", "Only Purchase Material Requests can be saved from this form.")

    forbidden = _payload_forbidden_keys(data)
    if forbidden:
        return _error("Purchase Request draft not saved", f"This form cannot set {', '.join(sorted(forbidden))}.")

    if name:
        if not _can_edit_purchase_request():
            return _restricted("You need Material Request write permission to update this Purchase Request draft.")
        doc = _get_purchase_request_doc(name)
        if not doc:
            return _unavailable("Purchase Request unavailable", "This draft is not available for editing.")
        if int(_document_value(doc, "docstatus", 0) or 0) != 0:
            return _error("Purchase Request draft not saved", "Submitted or cancelled Purchase Requests cannot be edited here.")
        if cstr(_document_value(doc, "material_request_type")).strip() != PURCHASE_TYPE:
            return _error("Purchase Request draft not saved", "Only Purchase Material Requests can be edited here.")
        if hasattr(doc, "check_permission"):
            doc.check_permission("write")
    else:
        if not _can_create_purchase_request():
            return _restricted("You need Material Request create permission to create a Purchase Request draft.")
        doc = frappe.get_doc({"doctype": DOCTYPE})

    transaction_date = _safe_date(header.get("transaction_date"))
    schedule_date = _safe_date(header.get("schedule_date"), transaction_date)
    company = cstr(header.get("company") or _default_company()).strip()
    normalized_items, item_error = _normalize_items(items, schedule_date)
    if item_error:
        return _error("Purchase Request draft not saved", item_error)
    if not company:
        return _unavailable("Company unavailable", "A default company is required before saving a Purchase Request draft.")

    _set_document_value(doc, "material_request_type", PURCHASE_TYPE)
    _set_document_value(doc, "transaction_date", transaction_date)
    _set_document_value(doc, "schedule_date", schedule_date)
    _set_document_value(doc, "company", company)
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
        if name:
            doc.save()
        else:
            doc.insert()
    except Exception as exc:
        return _error("Purchase Request draft not saved", cstr(exc) or "ERPNext validation stopped the draft save.")

    saved_name = cstr(_document_value(doc, "name", name)).strip()
    payload_out = _doc_to_form_payload(doc)
    payload_out["saved"] = True
    payload_out["message"] = f"Draft {saved_name} saved."
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
def get_managed_purchase_request_item_defaults(item_code: str | None = None) -> dict[str, object]:
    if not _has_procurement_form_access() or not common.can_read("Item"):
        return _restricted("You do not have Item read permission for Purchase Request item lookup.")
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
