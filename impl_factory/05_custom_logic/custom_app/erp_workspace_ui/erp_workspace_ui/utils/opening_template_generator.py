from __future__ import annotations

import json
from typing import Iterable

import frappe


SKIP_FIELD_TYPES = {
    "Section Break",
    "Column Break",
    "Tab Break",
    "Fold",
    "HTML",
    "Button",
    "Heading",
    "Image",
}

CHILD_FIELD_HINTS = {
    "item_code",
    "qty",
    "rate",
    "amount",
    "warehouse",
    "account",
    "cost_center",
    "debit_in_account_currency",
    "credit_in_account_currency",
    "uom",
    "income_account",
    "expense_account",
}


def generate_opening_template_headers(doctype: str) -> str:
    """Return a JSON-encoded list of template headers for a doctype."""
    meta = frappe.get_meta(doctype)
    headers: list[str] = []
    seen: set[str] = set()

    for field in meta.fields:
        if field.fieldtype in SKIP_FIELD_TYPES:
            continue
        if field.fieldtype == "Table":
            headers.extend(_table_headers(field.fieldname, field.options, seen))
            continue
        if field.fieldname and field.fieldname not in seen:
            headers.append(field.fieldname)
            seen.add(field.fieldname)

    return json.dumps(headers)


def _table_headers(parent_field: str, child_doctype: str, seen: set[str]) -> Iterable[str]:
    child_meta = frappe.get_meta(child_doctype)
    child_fields = []
    for child_field in child_meta.fields:
        if child_field.fieldtype in SKIP_FIELD_TYPES:
            continue
        if child_field.reqd or child_field.fieldname in CHILD_FIELD_HINTS:
            child_fields.append(child_field.fieldname)
    if not child_fields:
        child_fields = [
            cf.fieldname
            for cf in child_meta.fields
            if cf.fieldtype not in SKIP_FIELD_TYPES and cf.fieldname
        ]
    headers = []
    for fieldname in child_fields:
        key = f"{parent_field}.{fieldname}"
        if key in seen:
            continue
        headers.append(key)
        seen.add(key)
    return headers
