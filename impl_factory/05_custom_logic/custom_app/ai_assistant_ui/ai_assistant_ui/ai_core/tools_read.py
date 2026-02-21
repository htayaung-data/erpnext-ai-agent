import frappe


def _fac_tool_api():
    try:
        from frappe_assistant_core.utils import tool_api  # type: ignore
        return tool_api
    except Exception:
        return None


def report_list(module=None, report_type=None):
    fac = _fac_tool_api()
    if fac and hasattr(fac, "report_list"):
        return fac.report_list(module=module, report_type=report_type)

    filters = {}
    if module:
        filters["module"] = module
    if report_type:
        filters["report_type"] = report_type

    rows = frappe.get_all(
        "Report",
        filters=filters,
        fields=["name", "report_type", "module", "disabled", "ref_doctype"],
        order_by="module asc, name asc",
        limit=500,
    )
    return {"reports": rows}


def report_requirements(report_name, include_metadata=False, include_columns=True, include_filters=True):
    fac = _fac_tool_api()
    if fac and hasattr(fac, "report_requirements"):
        return fac.report_requirements(
            report_name=report_name,
            include_metadata=include_metadata,
            include_columns=include_columns,
            include_filters=include_filters,
        )

    rep = frappe.get_doc("Report", report_name)
    out = {"report_name": report_name, "report_type": rep.report_type, "module": rep.module}
    if include_filters:
        out["filters"] = rep.get("filters") or []
    if include_columns:
        out["columns"] = rep.get("columns") or []
    if include_metadata:
        out["metadata"] = {"disabled": rep.disabled, "ref_doctype": rep.ref_doctype, "modified": rep.modified}
    return out


def generate_report(report_name, filters=None, format="json"):
    """
    Prefer FAC generate_report (prepared reports supported).
    """
    fac = _fac_tool_api()
    if fac and hasattr(fac, "generate_report"):
        return fac.generate_report(report_name=report_name, filters=filters or {}, format=format)

    from frappe.desk.query_report import run  # type: ignore
    return run(report_name, filters=filters or {}, user=frappe.session.user)


def list_documents(doctype, filters=None, fields=None, limit=20, order_by=None):
    limit = min(int(limit or 20), 200)
    rows = frappe.get_all(
        doctype,
        filters=filters or {},
        fields=fields or ["name", "modified"],
        limit=limit,
        order_by=order_by or "modified desc",
    )
    return {"doctype": doctype, "rows": rows}


def get_document(doctype, name):
    doc = frappe.get_doc(doctype, name)
    return {"doctype": doctype, "doc": doc.as_dict()}


def search_link(doctype, query, filters=None):
    try:
        from frappe.desk.search import search_link  # type: ignore
        return {"doctype": doctype, "results": search_link(doctype=doctype, txt=query, filters=filters or {})}
    except Exception:
        rows = frappe.get_all(doctype, filters={"name": ["like", f"{query}%"]}, fields=["name"], limit=20)
        return {"doctype": doctype, "results": rows}


def search_doctype(doctype, query, limit=20):
    limit = min(int(limit or 20), 50)
    rows = frappe.get_all(
        doctype,
        filters={"name": ["like", f"%{query}%"]},
        fields=["name", "modified"],
        limit=limit,
        order_by="modified desc",
    )
    return {"doctype": doctype, "results": rows}


TOOL_REGISTRY_READ = {
    "report_list": report_list,
    "report_requirements": report_requirements,
    "generate_report": generate_report,
    "list_documents": list_documents,
    "get_document": get_document,
    "search_link": search_link,
    "search_doctype": search_doctype,
}
