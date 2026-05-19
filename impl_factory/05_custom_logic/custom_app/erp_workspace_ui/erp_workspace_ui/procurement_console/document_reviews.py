from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from . import common, document_output, readiness, service


def _clear_frappe_messages() -> None:
    try:
        if hasattr(frappe.local, "message_log"):
            frappe.local.message_log = []
    except Exception:
        pass
    try:
        response = getattr(frappe.local, "response", None)
        if isinstance(response, dict):
            response.pop("_server_messages", None)
    except Exception:
        pass


def _finalize_payload(payload: dict[str, object]) -> dict[str, object]:
    _clear_frappe_messages()
    return payload


MR_FIELDS = [
    "name",
    "title",
    "material_request_type",
    "company",
    "transaction_date",
    "schedule_date",
    "status",
    "workflow_state",
    "docstatus",
    "per_ordered",
    "per_received",
    "modified",
]

MR_ITEM_FIELDS = [
    "name",
    "parent",
    "item_code",
    "item_name",
    "description",
    "qty",
    "ordered_qty",
    "received_qty",
    "uom",
    "stock_uom",
    "schedule_date",
    "warehouse",
]

RFQ_FIELDS = [
    "name",
    "company",
    "transaction_date",
    "schedule_date",
    "status",
    "docstatus",
    "modified",
]

RFQ_ITEM_FIELDS = [
    "name",
    "parent",
    "item_code",
    "item_name",
    "description",
    "qty",
    "uom",
    "stock_uom",
    "schedule_date",
    "warehouse",
    "material_request",
]

RFQ_SUPPLIER_FIELDS = ["name", "parent", "supplier", "supplier_name", "quote_status", "email_id"]

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
    "request_for_quotation",
    "modified",
]

SQ_ITEM_FIELDS = [
    "name",
    "parent",
    "item_code",
    "item_name",
    "description",
    "qty",
    "uom",
    "stock_uom",
    "rate",
    "amount",
    "request_for_quotation",
    "material_request",
]


@frappe.whitelist()
def get_purchase_request_review_context(
    material_request: str | None = None,
    name: str | None = None,
    return_queue: str | None = None,
) -> dict[str, object]:
    service.ensure_authenticated()
    context = service.build_context()
    request_name = cstr(material_request or name).strip()
    back_queue = _back_queue(return_queue, "purchase_request_directory")
    if not service.has_procurement_access(context):
        return _finalize_payload(_state_payload("purchase_request_review", "Purchase Request Review", request_name, service.restricted_state(), back_queue, "Back to purchase requests"))
    if not request_name:
        return _finalize_payload(_state_payload(
            "purchase_request_review",
            "Purchase Request Review",
            request_name,
            common.unavailable_state("Purchase Request required", "Open a purchase request row to review sourcing demand."),
            back_queue,
            "Back to purchase requests",
        ))
    if not common.can_read("Material Request"):
        return _state_payload(
            "purchase_request_review",
            "Purchase Request Review",
            request_name,
            common.restricted_state("Purchase Request review restricted", "Material Request"),
            back_queue,
            "Back to purchase requests",
        )

    record = _visible_material_request(request_name)
    if not record:
        return _state_payload(
            "purchase_request_review",
            "Purchase Request Review",
            request_name,
            common.unavailable_state("Purchase Request not found", "The requested Purchase Material Request is not visible for this user."),
            back_queue,
            "Back to purchase requests",
        )
    return _finalize_payload(_purchase_request_payload(record, _material_request_items(request_name), context, back_queue))


@frappe.whitelist()
def get_rfq_review_context(
    request_for_quotation: str | None = None,
    name: str | None = None,
    return_queue: str | None = None,
) -> dict[str, object]:
    service.ensure_authenticated()
    context = service.build_context()
    rfq_name = cstr(request_for_quotation or name).strip()
    back_queue = _back_queue(return_queue, "rfq_directory")
    if not service.has_procurement_access(context):
        return _finalize_payload(_state_payload("rfq_review", "RFQ Review", rfq_name, service.restricted_state(), back_queue, "Back to RFQs"))
    if not rfq_name:
        return _finalize_payload(_state_payload("rfq_review", "RFQ Review", rfq_name, common.unavailable_state("RFQ required", "Open an RFQ row to review supplier response context."), back_queue, "Back to RFQs"))
    if not common.can_read("Request for Quotation"):
        return _finalize_payload(_state_payload("rfq_review", "RFQ Review", rfq_name, common.restricted_state("RFQ review restricted", "Request for Quotation"), back_queue, "Back to RFQs"))

    record = _visible_rfq(rfq_name)
    if not record:
        return _finalize_payload(_state_payload("rfq_review", "RFQ Review", rfq_name, common.unavailable_state("RFQ not found", "The requested RFQ is not visible for this user."), back_queue, "Back to RFQs"))
    return _finalize_payload(_rfq_payload(record, _rfq_items(rfq_name), _rfq_suppliers(rfq_name), context, back_queue))


@frappe.whitelist()
def get_supplier_quotation_review_context(
    supplier_quotation: str | None = None,
    name: str | None = None,
    return_queue: str | None = None,
) -> dict[str, object]:
    service.ensure_authenticated()
    context = service.build_context()
    quotation_name = cstr(supplier_quotation or name).strip()
    back_queue = _back_queue(return_queue, "supplier_quotation_directory")
    if not service.has_procurement_access(context):
        return _finalize_payload(_state_payload("supplier_quotation_review", "Supplier Quotation Review", quotation_name, service.restricted_state(), back_queue, "Back to supplier quotations"))
    if not quotation_name:
        return _state_payload(
            "supplier_quotation_review",
            "Supplier Quotation Review",
            quotation_name,
            common.unavailable_state("Supplier Quotation required", "Open a supplier quotation row to review the offer."),
            back_queue,
            "Back to supplier quotations",
        )
    if not common.can_read("Supplier Quotation"):
        return _state_payload(
            "supplier_quotation_review",
            "Supplier Quotation Review",
            quotation_name,
            common.restricted_state("Supplier Quotation review restricted", "Supplier Quotation"),
            back_queue,
            "Back to supplier quotations",
        )

    record = _visible_supplier_quotation(quotation_name)
    if not record:
        return _state_payload(
            "supplier_quotation_review",
            "Supplier Quotation Review",
            quotation_name,
            common.unavailable_state("Supplier Quotation not found", "The requested supplier quotation is not visible for this user."),
            back_queue,
            "Back to supplier quotations",
        )
    return _finalize_payload(_supplier_quotation_payload(record, _supplier_quotation_items(quotation_name), context, back_queue))


def _purchase_request_payload(record: dict[str, object], items: list[dict[str, object]], context: dict[str, object], back_queue: str) -> dict[str, object]:
    name = cstr(record.get("name"))
    actions, targets = _actions_and_targets("Material Request", name, context, back_queue, "Back to purchase requests", "ERP Purchase Request Form")
    return {
        "page": {"title": "Purchase Request Review", "key": "purchase_request_review", "name": name},
        "summary": {
            "kicker": "Purchase request review",
            "title": name,
            "subtitle": "Read-only buyer review of purchase demand before sourcing or ordering follow-up.",
            "chips": [{"label": "Read-only", "tone": "good"}, {"label": record.get("workflow_state") or record.get("status") or "Status", "tone": "pending"}],
            "facts": [
                {"label": "Request Type", "value": record.get("material_request_type") or "Purchase", "meta": record.get("company") or ""},
                {"label": "Required By", "value": cstr(record.get("schedule_date") or "--"), "meta": "Demand date"},
                {"label": "Ordered", "value": _percent(record.get("per_ordered")), "meta": "Sourcing posture"},
                {"label": "Received", "value": _percent(record.get("per_received")), "meta": "Downstream visibility"},
            ],
        },
        "controls": {"actions": actions},
        "detail": {"state": common.ready_state(), "readiness_context": readiness.get_purchase_request_readiness_context(name), "sections": [_section("Requested items", "Purchase demand lines visible to this buyer. Warehouse execution is not exposed here.", _material_request_item_table(items))]},
        "action_targets": targets,
        "context": {"role_variant": context.get("role_variant")},
    }


def _rfq_payload(record: dict[str, object], items: list[dict[str, object]], suppliers: list[dict[str, object]], context: dict[str, object], back_queue: str) -> dict[str, object]:
    name = cstr(record.get("name"))
    actions, targets = _actions_and_targets("Request for Quotation", name, context, back_queue, "Back to RFQs", "ERP RFQ Form")
    return {
        "page": {"title": "RFQ Review", "key": "rfq_review", "name": name},
        "summary": {
            "kicker": "RFQ review",
            "title": name,
            "subtitle": "Read-only sourcing review of RFQ dates, supplier response posture, and requested items.",
            "chips": [{"label": "Read-only", "tone": "good"}, {"label": record.get("status") or "Status", "tone": "pending"}],
            "facts": [
                {"label": "Company", "value": record.get("company") or "--", "meta": "Buying scope"},
                {"label": "RFQ Date", "value": cstr(record.get("transaction_date") or "--"), "meta": "Document date"},
                {"label": "Required By", "value": cstr(record.get("schedule_date") or "--"), "meta": "Supplier response context"},
                {"label": "Suppliers", "value": len(suppliers), "meta": "Visible invited suppliers"},
            ],
        },
        "controls": {"actions": actions},
        "detail": {
            "state": common.ready_state(),
            "readiness_context": readiness.get_rfq_readiness_context(name),
            "sections": [
                _section("Invited suppliers", "Supplier response posture from the RFQ supplier table.", _rfq_supplier_table(suppliers)),
                _section("Requested items", "Items and quantities included in this sourcing request.", _rfq_item_table(items)),
            ],
        },
        "output_context": document_output.get_document_output_context("Request for Quotation", name),
        "action_targets": targets,
        "context": {"role_variant": context.get("role_variant")},
    }


def _supplier_quotation_payload(record: dict[str, object], items: list[dict[str, object]], context: dict[str, object], back_queue: str) -> dict[str, object]:
    name = cstr(record.get("name"))
    actions, targets = _actions_and_targets("Supplier Quotation", name, context, back_queue, "Back to supplier quotations", "ERP Supplier Quotation Form")
    actions.append({"key": "open_quote_comparison", "title": "Compare offers", "label": "Compare offers", "variant": "secondary", "category": "navigation", "icon": "bar-chart"})
    targets["open_quote_comparison"] = {"kind": "report_page", "report_key": "supplier_quotation_comparison", "filters": {"supplier_quotation": name}}
    return {
        "page": {"title": "Supplier Quotation Review", "key": "supplier_quotation_review", "name": name},
        "summary": {
            "kicker": "Supplier quotation review",
            "title": name,
            "subtitle": "Read-only buyer review of supplier offer, validity, totals, and quoted items.",
            "chips": [{"label": "Read-only", "tone": "good"}, {"label": record.get("status") or "Status", "tone": "pending"}],
            "facts": [
                {"label": "Supplier", "value": record.get("supplier_name") or record.get("supplier") or "--", "meta": record.get("company") or ""},
                {"label": "Quotation Date", "value": cstr(record.get("transaction_date") or "--"), "meta": "Offer date"},
                {"label": "Valid Till", "value": cstr(record.get("valid_till") or "--"), "meta": "Buyer review window"},
                {"label": "Total", "value": _money(record.get("grand_total"), record.get("currency")), "meta": "Quoted total"},
            ],
        },
        "controls": {"actions": actions},
        "detail": {"state": common.ready_state(), "readiness_context": readiness.get_supplier_quotation_readiness_context(name), "sections": [_section("Quoted items", "Supplier rates, quantities, amount, and source references for buyer comparison.", _supplier_quotation_item_table(items))]},
        "action_targets": targets,
        "context": {"role_variant": context.get("role_variant")},
    }


def _state_payload(page_key: str, page_title: str, entity_name: str, state: dict[str, object], back_queue: str, back_label: str) -> dict[str, object]:
    return {
        "page": {"title": page_title, "key": page_key, "name": entity_name},
        "summary": {
            "kicker": "Procurement review",
            "title": entity_name or page_title,
            "subtitle": state.get("detail") or "This review page is not available.",
            "chips": [{"label": state.get("kind") or "state", "tone": "blocker" if state.get("kind") in {"restricted", "error"} else "neutral"}],
            "facts": [],
        },
        "controls": {"actions": _base_actions(back_label)},
        "detail": {"state": state, "sections": []},
        "action_targets": {"back_to_worklist": {"kind": "worklist", "queue_key": back_queue}},
    }


def _visible_material_request(name: str) -> dict[str, object] | None:
    rows = common.get_list(
        "Material Request",
        fields=_available_fields("Material Request", MR_FIELDS),
        filters=[["Material Request", "name", "=", name], ["Material Request", "material_request_type", "=", "Purchase"]],
        limit=1,
    )
    return dict(rows[0]) if rows else None


def _visible_rfq(name: str) -> dict[str, object] | None:
    rows = common.get_list("Request for Quotation", fields=_available_fields("Request for Quotation", RFQ_FIELDS), filters=[["Request for Quotation", "name", "=", name]], limit=1)
    return dict(rows[0]) if rows else None


def _visible_supplier_quotation(name: str) -> dict[str, object] | None:
    rows = common.get_list("Supplier Quotation", fields=_available_fields("Supplier Quotation", SQ_FIELDS), filters=[["Supplier Quotation", "name", "=", name]], limit=1)
    return dict(rows[0]) if rows else None


def _material_request_items(parent: str) -> list[dict[str, object]]:
    return _get_child_rows("Material Request Item", parent, MR_ITEM_FIELDS)


def _rfq_items(parent: str) -> list[dict[str, object]]:
    return _get_child_rows("Request for Quotation Item", parent, RFQ_ITEM_FIELDS)


def _rfq_suppliers(parent: str) -> list[dict[str, object]]:
    return _get_child_rows("Request for Quotation Supplier", parent, RFQ_SUPPLIER_FIELDS)


def _supplier_quotation_items(parent: str) -> list[dict[str, object]]:
    return _get_child_rows("Supplier Quotation Item", parent, SQ_ITEM_FIELDS)


def _get_child_rows(doctype: str, parent: str, fields: list[str]) -> list[dict[str, object]]:
    try:
        return list(frappe.get_all(doctype, filters={"parent": parent}, fields=_available_fields(doctype, fields), order_by="idx asc", limit_page_length=common.ROW_LIMIT))
    except Exception:
        return []


def _available_fields(doctype: str, fields: list[str]) -> list[str]:
    output = []
    for field in fields:
        if field in {"name", "parent"} or common.has_field(doctype, field):
            output.append(field)
    return output or ["name"]


def _actions_and_targets(doctype: str, name: str, context: dict[str, object], back_queue: str, back_label: str, native_leaf_label: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    actions = _base_actions(back_label)
    targets: dict[str, object] = {"back_to_worklist": {"kind": "worklist", "queue_key": back_queue}}
    return actions, targets


def _base_actions(back_label: str) -> list[dict[str, object]]:
    return [
        {"key": "back_to_worklist", "title": back_label, "label": back_label, "variant": "secondary", "category": "navigation", "icon": "arrow-left"},
        {"key": "refresh", "title": "Refresh", "label": "Refresh", "variant": "secondary", "icon": "refresh"},
    ]


def _back_queue(return_queue: str | None, fallback: str) -> str:
    return cstr(return_queue).strip() or fallback


def _section(title: str, note: str, table: dict[str, object], status: str = "Read-only") -> dict[str, object]:
    return {"title": title, "note": note, "status": status, "table": table}


def _material_request_item_table(rows: list[dict[str, object]]) -> dict[str, object]:
    return _table(
        [
            {"key": "item", "label": "Item"},
            {"key": "qty", "label": "Qty"},
            {"key": "ordered", "label": "Ordered"},
            {"key": "received", "label": "Received"},
            {"key": "required_by", "label": "Required By"},
            {"key": "warehouse", "label": "Warehouse"},
        ],
        [
            {
                "key": cstr(row.get("name") or row.get("item_code")),
                "cells": {
                    "item": {"value": row.get("item_code") or "-", "meta": row.get("item_name") or _clean_description(row.get("description"))},
                    "qty": _quantity(row.get("qty"), row.get("uom") or row.get("stock_uom")),
                    "ordered": _quantity(row.get("ordered_qty"), row.get("uom") or row.get("stock_uom")),
                    "received": _quantity(row.get("received_qty"), row.get("uom") or row.get("stock_uom")),
                    "required_by": cstr(row.get("schedule_date") or ""),
                    "warehouse": row.get("warehouse") or "-",
                },
            }
            for row in rows
        ],
        "No visible request items",
        "No visible Material Request Item rows are linked to this request.",
    )


def _rfq_item_table(rows: list[dict[str, object]]) -> dict[str, object]:
    return _table(
        [
            {"key": "item", "label": "Item"},
            {"key": "qty", "label": "Qty"},
            {"key": "required_by", "label": "Required By"},
            {"key": "warehouse", "label": "Warehouse"},
            {"key": "source", "label": "Source"},
        ],
        [
            {
                "key": cstr(row.get("name") or row.get("item_code")),
                "cells": {
                    "item": {"value": row.get("item_code") or "-", "meta": row.get("item_name") or _clean_description(row.get("description"))},
                    "qty": _quantity(row.get("qty"), row.get("uom") or row.get("stock_uom")),
                    "required_by": cstr(row.get("schedule_date") or ""),
                    "warehouse": row.get("warehouse") or "-",
                    "source": row.get("material_request") or "-",
                },
            }
            for row in rows
        ],
        "No visible RFQ items",
        "No visible Request for Quotation Item rows are linked to this RFQ.",
    )


def _rfq_supplier_table(rows: list[dict[str, object]]) -> dict[str, object]:
    return _table(
        [{"key": "supplier", "label": "Supplier"}, {"key": "response", "label": "Response"}, {"key": "email", "label": "Email"}],
        [
            {
                "key": cstr(row.get("name") or row.get("supplier")),
                "cells": {
                    "supplier": {"value": row.get("supplier_name") or row.get("supplier") or "-", "meta": row.get("supplier") or ""},
                    "response": row.get("quote_status") or "-",
                    "email": row.get("email_id") or "-",
                },
            }
            for row in rows
        ],
        "No visible invited suppliers",
        "No visible RFQ Supplier rows are linked to this RFQ.",
    )


def _supplier_quotation_item_table(rows: list[dict[str, object]]) -> dict[str, object]:
    return _table(
        [{"key": "item", "label": "Item"}, {"key": "qty", "label": "Qty"}, {"key": "rate", "label": "Rate"}, {"key": "amount", "label": "Amount"}, {"key": "references", "label": "References"}],
        [
            {
                "key": cstr(row.get("name") or row.get("item_code")),
                "cells": {
                    "item": {"value": row.get("item_code") or "-", "meta": row.get("item_name") or _clean_description(row.get("description"))},
                    "qty": _quantity(row.get("qty"), row.get("uom") or row.get("stock_uom")),
                    "rate": _money(row.get("rate"), ""),
                    "amount": _money(row.get("amount"), ""),
                    "references": _references(row.get("request_for_quotation"), row.get("material_request")),
                },
            }
            for row in rows
        ],
        "No visible quoted items",
        "No visible Supplier Quotation Item rows are linked to this quotation.",
    )


def _table(columns: list[dict[str, object]], rows: list[dict[str, object]], empty_title: str, empty_detail: str) -> dict[str, object]:
    return {"columns": columns, "rows": rows, "state": common.ready_state() if rows else common.empty_state(empty_title, empty_detail)}


def _references(*values: object) -> str:
    refs = [cstr(value).strip() for value in values if cstr(value).strip()]
    return ", ".join(refs) if refs else "-"


def _clean_description(value: object) -> str:
    return cstr(value).replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ").strip()


def _quantity(value: object, uom: object = "") -> str:
    number = flt(value)
    quantity = str(int(number)) if number.is_integer() else f"{number:,.2f}"
    unit = cstr(uom).strip()
    return f"{quantity} {unit}".strip()


def _percent(value: object) -> str:
    number = flt(value)
    return f"{int(number)}%" if number.is_integer() else f"{number:.1f}%"


def _money(value: object, currency: object) -> str:
    amount = flt(value)
    amount_text = f"{int(amount):,}" if amount.is_integer() else f"{amount:,.2f}"
    code = cstr(currency).strip()
    return f"{code} {amount_text}".strip() if code else amount_text
