from __future__ import annotations

import csv
import io
import time
from typing import Any, Dict, List, Optional

import frappe
from frappe.utils.file_manager import save_file


def _ts_suffix() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def save_table_exports(
    *,
    basename: str,
    columns: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    attach_to_doctype: Optional[str] = None,
    attach_to_name: Optional[str] = None,
    private: bool = True,
) -> Dict[str, str]:
    """
    Create CSV + XLSX files and store using File DocType via save_file().
    Returns {"csv": file_url, "xlsx": file_url}
    """
    attach_to_doctype = attach_to_doctype or "AI Chat Session"
    attach_to_name = attach_to_name or None

    labels = [c.get("label") or c.get("fieldname") for c in columns]
    fns = [c.get("fieldname") for c in columns]

    # ---- CSV
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow(labels)
    for r in rows:
        writer.writerow([r.get(fn) for fn in fns])

    csv_bytes = sio.getvalue().encode("utf-8")
    csv_name = f"{basename}_{_ts_suffix()}.csv"
    csv_file = save_file(
        fname=csv_name,
        content=csv_bytes,
        dt=attach_to_doctype,
        dn=attach_to_name,
        is_private=1 if private else 0,
    )

    # ---- XLSX
    try:
        import openpyxl  # noqa: F401
        from openpyxl import Workbook
    except Exception as e:
        frappe.log_error(
            title="ai_assistant_ui: openpyxl import failed",
            message=frappe.get_traceback(),
        )
        # still return CSV
        return {"csv": csv_file.file_url}

    wb = Workbook()
    ws = wb.active
    ws.title = "Report"

    ws.append(labels)
    for r in rows:
        ws.append([r.get(fn) for fn in fns])

    bio = io.BytesIO()
    wb.save(bio)
    xlsx_bytes = bio.getvalue()

    xlsx_name = f"{basename}_{_ts_suffix()}.xlsx"
    xlsx_file = save_file(
        fname=xlsx_name,
        content=xlsx_bytes,
        dt=attach_to_doctype,
        dn=attach_to_name,
        is_private=1 if private else 0,
    )

    return {"csv": csv_file.file_url, "xlsx": xlsx_file.file_url}
