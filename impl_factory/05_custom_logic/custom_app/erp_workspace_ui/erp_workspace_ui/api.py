"""API surface for UI workspace features."""

from __future__ import annotations

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import getdate, nowdate


@frappe.whitelist()
def get_sales_order_page_context(name: str) -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	if not name:
		frappe.throw(_("Sales Order is required"))

	doc = frappe.get_doc("Sales Order", name)
	if not doc.has_permission("read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	today = getdate(nowdate())
	delivery_names = _linked_delivery_names(doc.name)
	invoice_names = _linked_invoice_names(doc.name)
	return_docs = _linked_return_docs(delivery_names, invoice_names)
	todos = _linked_todos(doc.customer, doc.name, delivery_names, invoice_names, [row["name"] for row in return_docs])

	return {
		"summary": {
			"name": doc.name,
			"customer": doc.customer,
			"status": doc.status,
			"workflow_state": doc.get("workflow_state"),
			"owner": doc.owner,
			"owner_display": _user_display(doc.owner),
			"transaction_date": str(doc.transaction_date) if doc.transaction_date else None,
			"delivery_date": str(doc.delivery_date) if doc.delivery_date else None,
			"currency": doc.currency,
			"grand_total": float(doc.grand_total or 0),
			"per_delivered": float(doc.per_delivered or 0),
			"per_billed": float(doc.per_billed or 0),
			"billing_status": doc.get("billing_status"),
			"advance_payment_status": doc.get("advance_payment_status"),
			"source_quotation": _source_quotation_name(doc),
		},
		"linked_documents": {
			"quotation": _quotation_doc(_source_quotation_name(doc)),
			"deliveries": _doc_rows("Delivery Note", delivery_names, ["name", "status", "posting_date"]),
			"invoices": _doc_rows("Sales Invoice", invoice_names, ["name", "status", "posting_date", "outstanding_amount"]),
			"returns": return_docs,
		},
		"support": {
			"latest_task": todos[0] if todos else None,
			"open_task_count": len(todos),
			"approval_note": _sales_order_approval_note(doc),
			"customer_response_hint": _sales_order_customer_response_hint(doc, return_docs, today),
			"execution_note": _sales_order_execution_note(doc, today),
			"next_action": _sales_order_next_action(doc, return_docs, todos, today),
			"detail_guide": _sales_order_detail_guide(doc),
		},
	}


def _user_display(user: str | None) -> str | None:
	if not user:
		return None
	label = frappe.db.get_value("User", user, "full_name")
	return label or user


def _source_quotation_name(doc) -> str | None:
	for item in doc.get("items") or []:
		name = item.get("prevdoc_docname") or item.get("quotation")
		if name and frappe.db.exists("Quotation", name):
			return name
	return None


def _quotation_doc(name: str | None) -> dict[str, object] | None:
	if not name:
		return None
	rows = frappe.get_list("Quotation", filters={"name": name}, fields=["name", "status", "workflow_state"], limit_page_length=1)
	return rows[0] if rows else None


def _linked_delivery_names(sales_order: str) -> list[str]:
	parents = frappe.get_all(
		"Delivery Note Item",
		filters={"against_sales_order": sales_order},
		fields=["parent"],
		distinct=True,
		order_by="parent asc",
	)
	names = [row["parent"] for row in parents]
	if not names:
		return []
	visible = frappe.get_list(
		"Delivery Note",
		filters={"name": ["in", names], "docstatus": ["!=", 2], "is_return": ["!=", 1]},
		fields=["name"],
		order_by="posting_date asc, creation asc",
		limit_page_length=200,
	)
	index = {row["name"]: row["name"] for row in visible}
	return [name for name in names if name in index]


def _linked_invoice_names(sales_order: str) -> list[str]:
	parents = frappe.get_all(
		"Sales Invoice Item",
		filters={"sales_order": sales_order},
		fields=["parent"],
		distinct=True,
		order_by="parent asc",
	)
	names = [row["parent"] for row in parents]
	if not names:
		return []
	visible = frappe.get_list(
		"Sales Invoice",
		filters={"name": ["in", names], "docstatus": ["!=", 2], "is_return": ["!=", 1]},
		fields=["name"],
		order_by="posting_date asc, creation asc",
		limit_page_length=200,
	)
	return [row["name"] for row in visible]


def _linked_return_docs(delivery_names: list[str], invoice_names: list[str]) -> list[dict[str, object]]:
	results: list[dict[str, object]] = []
	if delivery_names:
		rows = frappe.get_list(
			"Delivery Note",
			filters={"is_return": 1, "return_against": ["in", delivery_names], "docstatus": ["!=", 2]},
			fields=["name", "status", "posting_date", "return_against"],
			order_by="posting_date desc, creation desc",
			limit_page_length=100,
		)
		results.extend({"doctype": "Delivery Note", **row} for row in rows)
	if invoice_names:
		rows = frappe.get_list(
			"Sales Invoice",
			filters={"is_return": 1, "return_against": ["in", invoice_names], "docstatus": ["!=", 2]},
			fields=["name", "status", "posting_date", "return_against"],
			order_by="posting_date desc, creation desc",
			limit_page_length=100,
		)
		results.extend({"doctype": "Sales Invoice", **row} for row in rows)
	return results


def _linked_todos(
	customer: str | None,
	sales_order: str,
	delivery_names: list[str],
	invoice_names: list[str],
	return_names: list[str],
) -> list[dict[str, object]]:
	reference_names = [sales_order]
	if customer:
		reference_names.append(customer)
	reference_names.extend(delivery_names)
	reference_names.extend(invoice_names)
	reference_names.extend(return_names)
	reference_names = [name for name in reference_names if name]
	if not reference_names:
		return []
	return frappe.get_list(
		"ToDo",
		filters={
			"status": ["!=", "Closed"],
			"reference_name": ["in", sorted(set(reference_names))],
			"reference_type": ["in", ["Customer", "Sales Order", "Delivery Note", "Sales Invoice"]],
		},
		fields=["name", "description", "allocated_to", "date", "reference_type", "reference_name"],
		order_by="date asc, creation asc",
		limit_page_length=50,
	)


def _doc_rows(doctype: str, names: list[str], fields: list[str]) -> list[dict[str, object]]:
	if not names:
		return []
	ordered_names = list(dict.fromkeys(name for name in names if name))
	rows = frappe.get_list(
		doctype,
		filters={"name": ["in", ordered_names], "docstatus": ["!=", 2]},
		fields=fields,
		order_by="posting_date asc, creation asc",
		limit_page_length=100,
	)
	index = {row["name"]: row for row in rows}
	return [index[name] for name in ordered_names if name in index]


def _sales_order_approval_note(doc) -> str:
	workflow_state = str(doc.get("workflow_state") or "").strip()
	if workflow_state in {"Pending Sales Approval", "Pending Executive Approval"}:
		reasons = []
		if float(doc.get("grand_total") or 0) >= 25000000:
			reasons.append("high order value")
		elif float(doc.get("grand_total") or 0) >= 10000000:
			reasons.append("manager approval threshold")
		if float(doc.get("additional_discount_percentage") or 0) > 0:
			reasons.append("additional discount")
		if float(doc.get("discount_amount") or 0) > 0:
			reasons.append("discount amount override")
		if reasons:
			return f"Approval is active because of {', '.join(reasons)}."
		return "Approval is active for this order and must be completed before normal processing."
	return "No active approval blocker is present on this order."


def _sales_order_execution_note(doc, today) -> str:
	per_delivered = float(doc.get("per_delivered") or 0)
	per_billed = float(doc.get("per_billed") or 0)
	delivery_date = getdate(doc.get("delivery_date")) if doc.get("delivery_date") else None
	if per_delivered and per_delivered < 100:
		return "This order is already moving through delivery and still needs completion."
	if per_delivered >= 100 and per_billed < 100:
		return "Delivery is complete, but billing is still unfinished."
	if delivery_date and delivery_date <= today + timedelta(days=3) and per_delivered == 0:
		return "Delivery commitment is approaching soon and needs close follow-through."
	return "The order is active in the commercial execution pipeline."


def _sales_order_customer_response_hint(doc, return_docs: list[dict[str, object]], today) -> str:
	workflow_state = str(doc.get("workflow_state") or "").strip()
	per_delivered = float(doc.get("per_delivered") or 0)
	per_billed = float(doc.get("per_billed") or 0)
	delivery_date = getdate(doc.get("delivery_date")) if doc.get("delivery_date") else None
	if workflow_state in {"Pending Sales Approval", "Pending Executive Approval"}:
		return "Tell the customer the order is under approval review before execution can proceed."
	if return_docs:
		return "Tell the customer a return-related case is already linked and under follow-up."
	if per_delivered and per_delivered < 100:
		return "Tell the customer the order is partially delivered and the remaining quantity is still being followed through."
	if per_delivered >= 100 and per_billed < 100:
		return "Tell the customer delivery is complete and billing finalization is still being followed."
	if delivery_date and delivery_date <= today + timedelta(days=3) and per_delivered == 0:
		return "Tell the customer the order is confirmed and aligned to an upcoming delivery commitment."
	return "Tell the customer the order is active and moving normally through the current execution flow."


def _sales_order_next_action(doc, return_docs: list[dict[str, object]], todos: list[dict[str, object]], today) -> str:
	workflow_state = str(doc.get("workflow_state") or "").strip()
	per_delivered = float(doc.get("per_delivered") or 0)
	per_billed = float(doc.get("per_billed") or 0)
	delivery_date = getdate(doc.get("delivery_date")) if doc.get("delivery_date") else None

	if workflow_state in {"Pending Sales Approval", "Pending Executive Approval"}:
		return "Complete the active approval step before promising further execution changes to the customer."
	if return_docs:
		return "Review the linked return activity and coordinate the next customer-facing response with operations or finance."
	if todos:
		task = todos[0]
		task_desc = task.get("description") or task.get("name")
		return f"Work the current follow-up task first: {task_desc}."
	if per_delivered >= 100 and per_billed < 100:
		return "Finish billing follow-through so the delivered order closes cleanly from a customer-communication view."
	if per_delivered > 0 and per_delivered < 100:
		return "Coordinate the remaining delivery and confirm the pending quantity or next shipment timing."
	if delivery_date and delivery_date <= today + timedelta(days=3) and per_delivered == 0:
		return "Confirm delivery preparation now because the customer commitment date is approaching soon."
	return "Continue normal execution follow-through and use the linked documents below when customer questions arise."


def _sales_order_detail_guide(doc) -> str:
	if doc.docstatus == 0:
		return "Use the detailed form sections below to complete items, taxes, addresses, and terms before submitting the order."
	return "Use the detailed form sections below for precise maintenance while keeping the execution summary above as the main working guide."
