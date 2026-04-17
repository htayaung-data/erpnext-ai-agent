from __future__ import annotations

import json
from typing import Any, Dict, List

import frappe


def validate_opening_documents(payload_path: str) -> str:
    """Validate opening-layer documents without inserting them."""
    with open(payload_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    report = {"validated": [], "errors": []}
    for doctype, rows in _iter_documents(payload.get("documents", {})):
        for idx, row in enumerate(rows, start=1):
            try:
                doc = _row_to_doc(doctype, row)
                doc.flags.ignore_permissions = True
                doc._action = "save"
                if doc.doctype in ("Sales Invoice", "Purchase Invoice"):
                    doc.run_method("set_missing_values")
                    if hasattr(doc, "calculate_taxes_and_totals"):
                        doc.calculate_taxes_and_totals()
                doc._doc_before_save = doc.as_dict()
                doc._validate()
                report["validated"].append(
                    {"doctype": doctype, "row": idx, "name": doc.get("name")}
                )
            except Exception as exc:  # pylint: disable=broad-except
                report["errors"].append(
                    {"doctype": doctype, "row": idx, "error": str(exc)}
                )

    output_path = payload.get("report_path")
    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)

    return json.dumps(report)


def _iter_documents(documents: Any):
    if isinstance(documents, list):
        for entry in documents:
            doctype = entry.get("doctype")
            rows = entry.get("rows", [])
            if doctype and rows:
                yield doctype, rows
        return

    if isinstance(documents, dict):
        for doctype, rows in documents.items():
            if rows:
                yield doctype, rows


def _row_to_doc(doctype: str, row: Dict[str, Any]):
    doc = frappe.new_doc(doctype)
    child_tables: Dict[str, Dict[str, Any]] = {}

    for key, value in row.items():
        if value in ("", None):
            continue
        if "." in key:
            parent, field = key.split(".", 1)
            child_tables.setdefault(parent, {})[field] = value
        else:
            doc.set(key, value)

    doc.set_new_name()
    for parent, fields in child_tables.items():
        if fields:
            doc.append(parent, fields)

    return doc
