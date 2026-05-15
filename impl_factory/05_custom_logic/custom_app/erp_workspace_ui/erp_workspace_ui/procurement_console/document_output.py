from __future__ import annotations

import re
from typing import Any

import frappe
from frappe.utils import cstr

from . import common, service


RFQ_DOCTYPE = "Request for Quotation"
PO_DOCTYPE = "Purchase Order"
ALLOWED_DOCTYPES = {RFQ_DOCTYPE, PO_DOCTYPE}

RFQ_WARNING = "Draft / Not sent"
PO_WARNING = "Draft / Not for supplier"
RFQ_SEND_BLOCK = "Email send requires a governed RFQ send step. This draft has not been sent to suppliers."
PO_SEND_BLOCK = "Supplier send requires approved/submitted purchase order governance. This draft is not a supplier commitment."


def _state(kind: str, title: str, detail: str = "") -> dict[str, str]:
    return {"kind": kind, "title": title, "detail": detail}


def _ready(title: str = "Ready") -> dict[str, str]:
    return _state("ready", title)


def _restricted(detail: str | None = None) -> dict[str, object]:
    return {
        "state": _state(
            "restricted",
            "Document output restricted",
            detail or "You do not have permission to use Procurement document output.",
        )
    }


def _error(title: str, detail: str) -> dict[str, object]:
    return {"state": _state("error", title, detail)}


def _authenticated_user() -> bool:
    return cstr(getattr(frappe.session, "user", "")).strip() not in {"", "Guest"}


def _has_procurement_output_access() -> bool:
    return _authenticated_user() and service.has_procurement_access()


def _validate_doctype(doctype: str) -> str:
    value = cstr(doctype).strip()
    if value not in ALLOWED_DOCTYPES:
        raise ValueError("Unsupported Procurement output document type.")
    return value


def _get_doc(doctype: str, name: str):
    docname = cstr(name).strip()
    if not docname or docname.lower() == "new":
        raise LookupError("Save the document before using supplier-facing output.")
    return frappe.get_doc(doctype, docname)


def _check_read_permission(doc: object) -> None:
    doctype = cstr(getattr(doc, "doctype", "")).strip()
    if not _has_procurement_output_access() or not common.can_read(doctype):
        raise PermissionError("Procurement document output requires read access.")
    if hasattr(doc, "check_permission"):
        doc.check_permission("read")


def _doc_value(doc: object, fieldname: str, default: Any = None) -> Any:
    if isinstance(doc, dict):
        return doc.get(fieldname, default)
    return getattr(doc, fieldname, default)


def _child_value(row: object, fieldname: str, default: Any = "") -> Any:
    if isinstance(row, dict):
        return row.get(fieldname, default)
    return getattr(row, fieldname, default)


def _safe_filename_part(value: Any) -> str:
    text = cstr(value).strip()
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-._")
    return text or "document"


def _print_formats_for(doctype: str) -> list[dict[str, str]]:
    rows = common.get_list(
        "Print Format",
        fields=["name", "print_format_type"],
        filters=[["Print Format", "doc_type", "=", doctype], ["Print Format", "disabled", "=", 0]],
        order_by="standard desc, name asc",
        limit=20,
    )
    formats: list[dict[str, str]] = []
    for row in rows:
        name = cstr(row.get("name")).strip()
        if name:
            formats.append({"name": name, "label": name, "type": cstr(row.get("print_format_type")).strip()})
    if not formats:
        formats.append({"name": "Standard", "label": "Standard", "type": "Standard"})
    return formats


def _letterheads() -> list[dict[str, str]]:
    rows = common.get_list(
        "Letter Head",
        fields=["name", "is_default"],
        filters=[["Letter Head", "disabled", "=", 0]],
        order_by="is_default desc, name asc",
        limit=20,
    )
    return [
        {"name": cstr(row.get("name")).strip(), "label": cstr(row.get("name")).strip(), "is_default": bool(row.get("is_default"))}
        for row in rows
        if cstr(row.get("name")).strip()
    ]


def _rfq_suppliers(doc: object) -> list[dict[str, str]]:
    suppliers: list[dict[str, str]] = []
    for row in list(_doc_value(doc, "suppliers", []) or []):
        supplier = cstr(_child_value(row, "supplier")).strip()
        if not supplier:
            continue
        supplier_name = cstr(_child_value(row, "supplier_name") or supplier).strip()
        suppliers.append(
            {
                "supplier": supplier,
                "supplier_name": supplier_name,
                "contact": cstr(_child_value(row, "contact")).strip(),
                "email_id": cstr(_child_value(row, "email_id")).strip(),
                "quote_status": cstr(_child_value(row, "quote_status")).strip(),
            }
        )
    return suppliers


def _po_supplier(doc: object) -> dict[str, str]:
    supplier = cstr(_doc_value(doc, "supplier")).strip()
    return {
        "supplier": supplier,
        "supplier_name": cstr(_doc_value(doc, "supplier_name") or supplier).strip(),
        "contact": cstr(_doc_value(doc, "contact_person")).strip(),
        "email_id": cstr(_doc_value(doc, "contact_email")).strip(),
    }


def _selected_rfq_supplier(doc: object, supplier: str | None) -> dict[str, str]:
    selected = cstr(supplier).strip()
    suppliers = _rfq_suppliers(doc)
    if not suppliers:
        raise ValueError("RFQ output needs at least one supplier.")
    if not selected and len(suppliers) == 1:
        selected = suppliers[0]["supplier"]
    if not selected:
        raise ValueError("Select one supplier before previewing or downloading an RFQ PDF.")
    for row in suppliers:
        if row["supplier"] == selected:
            return row
    raise ValueError("Selected supplier is not part of this RFQ.")


def _prepare_rfq_supplier_context(doc: object, supplier: str) -> None:
    if hasattr(doc, "update_supplier_part_no"):
        doc.update_supplier_part_no(supplier)
    else:
        setattr(doc, "vendor", supplier)


def _warning_for(doctype: str) -> str:
    return RFQ_WARNING if doctype == RFQ_DOCTYPE else PO_WARNING


def _send_block_for(doctype: str) -> str:
    return RFQ_SEND_BLOCK if doctype == RFQ_DOCTYPE else PO_SEND_BLOCK


def _filename_for(doctype: str, name: str, supplier: str | None = None) -> str:
    docname = _safe_filename_part(name)
    if doctype == RFQ_DOCTYPE:
        return f"{docname}-{_safe_filename_part(supplier)}-DRAFT-NOT-SENT.pdf"
    return f"{docname}-DRAFT-NOT-FOR-SUPPLIER.pdf"


def _output_context(doc: object, supplier: str | None = None) -> dict[str, object]:
    doctype = _validate_doctype(_doc_value(doc, "doctype"))
    name = cstr(_doc_value(doc, "name")).strip()
    base: dict[str, object] = {
        "state": _ready("Document output ready"),
        "doctype": doctype,
        "name": name,
        "docstatus": int(_doc_value(doc, "docstatus", 0) or 0),
        "status": cstr(_doc_value(doc, "status") or ("Draft" if int(_doc_value(doc, "docstatus", 0) or 0) == 0 else "")).strip(),
        "warning": _warning_for(doctype),
        "can_preview": True,
        "can_download_pdf": True,
        "can_send": False,
        "send_block_reason": _send_block_for(doctype),
        "print_formats": _print_formats_for(doctype),
        "letterheads": _letterheads(),
        "actions": [
            {"key": "preview", "label": "Preview RFQ" if doctype == RFQ_DOCTYPE else "Preview Purchase Order", "kind": "secondary"},
            {"key": "download_pdf", "label": "Download RFQ PDF" if doctype == RFQ_DOCTYPE else "Download PO PDF", "kind": "secondary"},
            {
                "key": "send",
                "label": "Email suppliers" if doctype == RFQ_DOCTYPE else "Email supplier",
                "kind": "blocked",
                "disabled": True,
                "reason": _send_block_for(doctype),
            },
        ],
    }
    if doctype == RFQ_DOCTYPE:
        suppliers = _rfq_suppliers(doc)
        base["suppliers"] = suppliers
        base["selected_supplier"] = supplier or (suppliers[0]["supplier"] if len(suppliers) == 1 else "")
        base["requires_supplier_selection"] = len(suppliers) != 1 or not base["selected_supplier"]
        base["filename_preview"] = _filename_for(doctype, name, cstr(base["selected_supplier"]).strip() or "SUPPLIER")
    else:
        base["supplier"] = _po_supplier(doc)
        base["filename_preview"] = _filename_for(doctype, name)
    return base


def _render_print_html(doc: object, print_format: str | None = None, letterhead: str | None = None) -> str:
    doctype = cstr(_doc_value(doc, "doctype")).strip()
    name = cstr(_doc_value(doc, "name")).strip()
    get_print = getattr(frappe, "get_print", None)
    if callable(get_print):
        return cstr(
            get_print(
                doctype,
                name,
                print_format or None,
                doc=doc,
                as_pdf=False,
                letterhead=letterhead or None,
            )
        )
    return f"<div class=\"print-format\"><h1>{doctype} {name}</h1></div>"


def _wrap_preview_html(doctype: str, name: str, html: str, supplier: str | None = None) -> str:
    warning = _warning_for(doctype)
    supplier_html = f"<div class=\"erpw-output-preview-supplier\">Supplier: {cstr(supplier)}</div>" if supplier else ""
    return f"""
<section class=\"erpw-output-preview\" data-doctype=\"{cstr(doctype)}\" data-name=\"{cstr(name)}\">
  <div class=\"erpw-output-preview-banner\">{warning}</div>
  {supplier_html}
  <div class=\"erpw-output-preview-body\">{html}</div>
</section>
""".strip()


def _html_to_pdf(html: str) -> bytes:
    try:
        from frappe.utils.pdf import get_pdf

        return get_pdf(html)
    except Exception:
        return html.encode("utf-8")


def _set_pdf_response(filename: str, content: bytes) -> None:
    if not hasattr(frappe, "local") or frappe.local is None:
        frappe.local = frappe._dict() if hasattr(frappe, "_dict") else type("Local", (), {})()
    if not hasattr(frappe.local, "response"):
        frappe.local.response = {}
    response = frappe.local.response
    try:
        response["filename"] = filename
        response["filecontent"] = content
        response["type"] = "pdf"
    except TypeError:
        setattr(response, "filename", filename)
        setattr(response, "filecontent", content)
        setattr(response, "type", "pdf")


@frappe.whitelist()
def get_document_output_context(doctype: str, name: str) -> dict[str, object]:
    try:
        doctype = _validate_doctype(doctype)
        doc = _get_doc(doctype, name)
        _check_read_permission(doc)
        return _output_context(doc)
    except PermissionError as exc:
        return _restricted(cstr(exc))
    except Exception as exc:
        return _error("Document output unavailable", cstr(exc))


@frappe.whitelist()
def get_document_print_preview_context(
    doctype: str,
    name: str,
    supplier: str | None = None,
    print_format: str | None = None,
    letterhead: str | None = None,
) -> dict[str, object]:
    try:
        doctype = _validate_doctype(doctype)
        doc = _get_doc(doctype, name)
        _check_read_permission(doc)
        selected_supplier: dict[str, str] | None = None
        if doctype == RFQ_DOCTYPE:
            selected_supplier = _selected_rfq_supplier(doc, supplier)
            _prepare_rfq_supplier_context(doc, selected_supplier["supplier"])
        html = _render_print_html(doc, print_format=print_format, letterhead=letterhead)
        wrapped = _wrap_preview_html(doctype, cstr(_doc_value(doc, "name")).strip(), html, selected_supplier["supplier"] if selected_supplier else None)
        context = _output_context(doc, selected_supplier["supplier"] if selected_supplier else None)
        context.update(
            {
                "html": wrapped,
                "selected_supplier": selected_supplier or context.get("selected_supplier", ""),
                "filename": _filename_for(doctype, cstr(_doc_value(doc, "name")).strip(), selected_supplier["supplier"] if selected_supplier else None),
            }
        )
        return context
    except PermissionError as exc:
        return _restricted(cstr(exc))
    except Exception as exc:
        return _error("Document preview unavailable", cstr(exc))


@frappe.whitelist()
def download_document_pdf(
    doctype: str,
    name: str,
    supplier: str | None = None,
    print_format: str | None = None,
    letterhead: str | None = None,
) -> None:
    doctype = _validate_doctype(doctype)
    doc = _get_doc(doctype, name)
    _check_read_permission(doc)
    selected_supplier: dict[str, str] | None = None
    if doctype == RFQ_DOCTYPE:
        selected_supplier = _selected_rfq_supplier(doc, supplier)
        _prepare_rfq_supplier_context(doc, selected_supplier["supplier"])
    html = _render_print_html(doc, print_format=print_format, letterhead=letterhead)
    wrapped = _wrap_preview_html(doctype, cstr(_doc_value(doc, "name")).strip(), html, selected_supplier["supplier"] if selected_supplier else None)
    filename = _filename_for(doctype, cstr(_doc_value(doc, "name")).strip(), selected_supplier["supplier"] if selected_supplier else None)
    _set_pdf_response(filename, _html_to_pdf(wrapped))
    return None
