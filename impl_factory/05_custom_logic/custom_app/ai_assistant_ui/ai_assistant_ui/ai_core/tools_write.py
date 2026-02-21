import frappe


def create_document(doctype, data, submit=False, validate_only=False):
    doc = frappe.get_doc({"doctype": doctype, **(data or {})})
    if validate_only:
        doc.run_method("validate")
        return {"status": "validated", "doctype": doctype, "doc": doc.as_dict()}
    doc.insert()
    if submit:
        doc.submit()
    return {"status": "created", "doctype": doctype, "name": doc.name, "docstatus": doc.docstatus}


def update_document(doctype, name, data):
    doc = frappe.get_doc(doctype, name)
    for k, v in (data or {}).items():
        doc.set(k, v)
    doc.save()
    return {"status": "updated", "doctype": doctype, "name": doc.name}


def delete_document(doctype, name, force=False):
    frappe.delete_doc(doctype, name, force=1 if force else 0)
    return {"status": "deleted", "doctype": doctype, "name": name}


def submit_document(doctype, name):
    doc = frappe.get_doc(doctype, name)
    doc.submit()
    return {"status": "submitted", "doctype": doctype, "name": doc.name, "docstatus": doc.docstatus}


def run_workflow(doctype, name, action, workflow=None):
    from frappe.model.workflow import apply_workflow  # type: ignore
    doc = frappe.get_doc(doctype, name)
    apply_workflow(doc, action)
    doc.reload()
    return {"status": "workflow_applied", "doctype": doctype, "name": doc.name, "workflow_state": getattr(doc, "workflow_state", None), "docstatus": doc.docstatus}


TOOL_REGISTRY_WRITE = {
    "create_document": create_document,
    "update_document": update_document,
    "delete_document": delete_document,
    "submit_document": submit_document,
    "run_workflow": run_workflow,
}
