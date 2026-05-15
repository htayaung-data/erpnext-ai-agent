from __future__ import annotations

import html
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
PO_SEND_BLOCK = "Supplier send requires a governed purchase order release step. This draft is not a supplier commitment."


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
                "label": "RFQ send deferred" if doctype == RFQ_DOCTYPE else "PO send deferred",
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


def _html(value: Any) -> str:
    return html.escape(cstr(value), quote=True)


def _number(value: Any) -> str:
    try:
        number = float(value or 0)
    except Exception:
        return _html(value)
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.2f}"


def _money(value: Any, currency: str | None = None) -> str:
    amount = _number(value)
    return f"{_html(currency)} {amount}" if currency else amount


def _preview_styles() -> str:
    return """
<style>
  .erpw-output-preview { color: #172033; font-family: Inter, Arial, sans-serif; }
  .erpw-output-preview-banner { display: inline-flex; margin-bottom: 12px; padding: 5px 10px; border-radius: 999px; border: 1px solid #b78b2a; background: #fff7e1; color: #67430a; font-size: 12px; font-weight: 700; letter-spacing: 0; }
  .erpw-output-preview-head { display: flex; justify-content: space-between; gap: 18px; border-bottom: 1px solid #e1e7ef; padding-bottom: 14px; margin-bottom: 14px; }
  .erpw-output-preview-title { font-size: 18px; font-weight: 760; margin: 0 0 4px; }
  .erpw-output-preview-subtitle { color: #526174; font-size: 12px; margin: 0; }
  .erpw-output-preview-meta { display: grid; grid-template-columns: repeat(2, minmax(120px, 1fr)); gap: 8px 16px; min-width: 280px; font-size: 12px; }
  .erpw-output-preview-meta span { display: block; color: #6b7888; font-size: 10px; font-weight: 700; text-transform: uppercase; }
  .erpw-output-preview-party { border: 1px solid #e1e7ef; border-radius: 8px; padding: 10px 12px; margin-bottom: 14px; background: #fbfcfe; font-size: 12px; }
  .erpw-output-preview-party strong { display: block; font-size: 13px; color: #172033; margin-bottom: 3px; }
  .erpw-output-preview-note { color: #526174; font-size: 12px; margin: 0 0 12px; }
  .erpw-output-preview-table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 11px; }
  .erpw-output-preview-table th { text-align: left; color: #5e6d7f; font-size: 10px; text-transform: uppercase; border-bottom: 1px solid #dbe3ec; padding: 7px 6px; background: #f7f9fc; }
  .erpw-output-preview-table td { border-bottom: 1px solid #edf1f5; padding: 8px 6px; vertical-align: top; overflow-wrap: anywhere; }
  .erpw-output-preview-table .num { text-align: right; white-space: nowrap; }
  .erpw-output-preview-total { display: flex; justify-content: flex-end; margin-top: 12px; font-size: 13px; font-weight: 760; }
  .erpw-output-preview-total span { min-width: 180px; text-align: right; }
</style>
""".strip()


def _item_label(row: object) -> str:
    code = cstr(_child_value(row, "item_code")).strip()
    name = cstr(_child_value(row, "item_name")).strip()
    if code and name and code != name:
        return f"{code} - {name}"
    return code or name or "Item"


def _productized_rfq_html(doc: object, selected_supplier: dict[str, str]) -> str:
    rows = []
    for row in list(_doc_value(doc, "items", []) or []):
        rows.append(
            "<tr>"
            f"<td>{_html(_item_label(row))}</td>"
            f"<td class='num'>{_number(_child_value(row, 'qty'))}</td>"
            f"<td>{_html(_child_value(row, 'uom') or _child_value(row, 'stock_uom'))}</td>"
            f"<td>{_html(_child_value(row, 'schedule_date') or _doc_value(doc, 'schedule_date'))}</td>"
            f"<td>{_html(_child_value(row, 'warehouse'))}</td>"
            "</tr>"
        )
    supplier_name = selected_supplier.get("supplier_name") or selected_supplier.get("supplier")
    supplier_contact = selected_supplier.get("contact") or ""
    supplier_email = selected_supplier.get("email_id") or ""
    return f"""
<div class="erpw-output-preview-head">
  <div>
    <h2 class="erpw-output-preview-title">Request for Quotation {_html(_doc_value(doc, 'name'))}</h2>
    <p class="erpw-output-preview-subtitle">Supplier-specific draft preview. This RFQ has not been sent.</p>
  </div>
  <div class="erpw-output-preview-meta">
    <div><span>Transaction Date</span>{_html(_doc_value(doc, 'transaction_date'))}</div>
    <div><span>Required By</span>{_html(_doc_value(doc, 'schedule_date'))}</div>
  </div>
</div>
<div class="erpw-output-preview-party">
  <strong>Supplier: {_html(supplier_name)}</strong>
  <div>{_html(selected_supplier.get('supplier'))}</div>
  <div>{_html(supplier_contact)}</div>
  <div>{_html(supplier_email)}</div>
</div>
<p class="erpw-output-preview-note">{_html(_doc_value(doc, 'subject') or 'Request for Quotation')}</p>
<table class="erpw-output-preview-table">
  <thead><tr><th style="width:42%">Item</th><th style="width:10%" class="num">Qty</th><th style="width:12%">UOM</th><th style="width:18%">Required By</th><th style="width:18%">Warehouse</th></tr></thead>
  <tbody>{''.join(rows) or '<tr><td colspan="5">No items</td></tr>'}</tbody>
</table>
""".strip()


def _productized_po_html(doc: object) -> str:
    currency = cstr(_doc_value(doc, "currency") or "MMK").strip()
    rows = []
    total = 0.0
    for row in list(_doc_value(doc, "items", []) or []):
        qty = _child_value(row, "qty")
        rate = _child_value(row, "rate")
        amount = _child_value(row, "amount")
        try:
            computed_amount = float(amount if amount not in (None, "") else float(qty or 0) * float(rate or 0))
        except Exception:
            computed_amount = 0.0
        total += computed_amount
        rows.append(
            "<tr>"
            f"<td>{_html(_item_label(row))}</td>"
            f"<td class='num'>{_number(qty)}</td>"
            f"<td>{_html(_child_value(row, 'uom') or _child_value(row, 'stock_uom'))}</td>"
            f"<td>{_html(_child_value(row, 'schedule_date') or _doc_value(doc, 'schedule_date'))}</td>"
            f"<td>{_html(_child_value(row, 'warehouse') or _doc_value(doc, 'set_warehouse'))}</td>"
            f"<td class='num'>{_money(rate, currency)}</td>"
            f"<td class='num'>{_money(computed_amount, currency)}</td>"
            "</tr>"
        )
    supplier = _po_supplier(doc)
    return f"""
<div class="erpw-output-preview-head">
  <div>
    <h2 class="erpw-output-preview-title">Purchase Order {_html(_doc_value(doc, 'name'))}</h2>
    <p class="erpw-output-preview-subtitle">Internal draft preview. This is not a supplier commitment.</p>
  </div>
  <div class="erpw-output-preview-meta">
    <div><span>Transaction Date</span>{_html(_doc_value(doc, 'transaction_date'))}</div>
    <div><span>Required By</span>{_html(_doc_value(doc, 'schedule_date'))}</div>
    <div><span>Currency</span>{_html(currency)}</div>
  </div>
</div>
<div class="erpw-output-preview-party">
  <strong>Supplier: {_html(supplier.get('supplier_name') or supplier.get('supplier'))}</strong>
  <div>{_html(supplier.get('supplier'))}</div>
  <div>{_html(supplier.get('contact'))}</div>
  <div>{_html(supplier.get('email_id'))}</div>
</div>
<table class="erpw-output-preview-table">
  <thead><tr><th style="width:30%">Item</th><th style="width:8%" class="num">Qty</th><th style="width:10%">UOM</th><th style="width:14%">Required By</th><th style="width:16%">Warehouse</th><th style="width:11%" class="num">Rate</th><th style="width:11%" class="num">Amount</th></tr></thead>
  <tbody>{''.join(rows) or '<tr><td colspan="7">No items</td></tr>'}</tbody>
</table>
<div class="erpw-output-preview-total">Total <span>{_money(total, currency)}</span></div>
""".strip()


def _render_productized_html(doc: object, selected_supplier: dict[str, str] | None = None) -> str:
    doctype = _validate_doctype(_doc_value(doc, "doctype"))
    if doctype == RFQ_DOCTYPE:
        return _productized_rfq_html(doc, selected_supplier or {})
    return _productized_po_html(doc)


def _wrap_preview_html(doctype: str, name: str, html_body: str, supplier: str | None = None) -> str:
    warning = _warning_for(doctype)
    supplier_html = f"<div class=\"erpw-output-preview-supplier\">Supplier: {_html(supplier)}</div>" if supplier else ""
    return f"""
<section class="erpw-output-preview" data-doctype="{_html(doctype)}" data-name="{_html(name)}">
  {_preview_styles()}
  <div class="erpw-output-preview-banner">{_html(warning)}</div>
  {supplier_html}
  <div class="erpw-output-preview-body">{html_body}</div>
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
        html = _render_productized_html(doc, selected_supplier)
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
    html = _render_productized_html(doc, selected_supplier)
    wrapped = _wrap_preview_html(doctype, cstr(_doc_value(doc, "name")).strip(), html, selected_supplier["supplier"] if selected_supplier else None)
    filename = _filename_for(doctype, cstr(_doc_value(doc, "name")).strip(), selected_supplier["supplier"] if selected_supplier else None)
    _set_pdf_response(filename, _html_to_pdf(wrapped))
    return None
