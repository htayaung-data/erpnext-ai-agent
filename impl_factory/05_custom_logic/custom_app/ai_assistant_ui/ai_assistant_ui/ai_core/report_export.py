import csv
import io
from datetime import datetime

from frappe.utils.file_manager import save_file
from openpyxl import Workbook


def _clean_filename(name: str) -> str:
    name = (name or "report").strip().replace("/", "-").replace("\\", "-")
    name = "".join(ch for ch in name if ch.isalnum() or ch in (" ", "-", "_")).strip().replace(" ", "_")
    return name or "report"


def _columns_to_labels(columns):
    labels = []
    if not columns:
        return labels
    for c in columns:
        if isinstance(c, dict):
            labels.append(c.get("label") or c.get("fieldname") or "Column")
        else:
            labels.append(str(c))
    return labels


def export_report_csv(report_name: str, columns, rows) -> dict:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{_clean_filename(report_name)}_{ts}.csv"

    out = io.StringIO()
    w = csv.writer(out)
    labels = _columns_to_labels(columns)
    if labels:
        w.writerow(labels)

    for r in rows or []:
        if isinstance(r, (list, tuple)):
            w.writerow(list(r))
        elif isinstance(r, dict):
            # best-effort: write dict values in column fieldname order if available
            if columns and all(isinstance(c, dict) for c in columns):
                w.writerow([r.get(c.get("fieldname")) for c in columns])
            else:
                w.writerow(list(r.values()))
        else:
            w.writerow([str(r)])

    content = out.getvalue().encode("utf-8")
    file_doc = save_file(filename, content, dt=None, dn=None, is_private=1)
    return {"file_url": file_doc.file_url, "file_name": filename}


def export_report_xlsx(report_name: str, columns, rows) -> dict:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{_clean_filename(report_name)}_{ts}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "Report"

    labels = _columns_to_labels(columns)
    if labels:
        ws.append(labels)

    fieldnames = []
    if columns and all(isinstance(c, dict) for c in columns):
        fieldnames = [c.get("fieldname") for c in columns]

    for r in rows or []:
        if isinstance(r, (list, tuple)):
            ws.append(list(r))
        elif isinstance(r, dict) and fieldnames:
            ws.append([r.get(fn) for fn in fieldnames])
        elif isinstance(r, dict):
            ws.append(list(r.values()))
        else:
            ws.append([str(r)])

    buff = io.BytesIO()
    wb.save(buff)

    file_doc = save_file(filename, buff.getvalue(), dt=None, dn=None, is_private=1)
    return {"file_url": file_doc.file_url, "file_name": filename}
