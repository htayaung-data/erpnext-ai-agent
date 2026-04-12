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


@frappe.whitelist()
def get_quotation_page_context(name: str) -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	if not name:
		frappe.throw(_("Quotation is required"))

	doc = frappe.get_doc("Quotation", name)
	if not doc.has_permission("read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	today = getdate(nowdate())
	sales_order_names = _linked_sales_order_names_from_quotation(doc.name)
	delivery_names = _linked_delivery_names_from_sales_orders(sales_order_names)
	invoice_names = _linked_invoice_names_from_sales_orders(sales_order_names)
	party = _quotation_party_doc(doc)
	opportunity = _linked_doc("Opportunity", doc.get("opportunity"), ["name", "status"])
	todos = _linked_reference_todos(
		[
			("Quotation", doc.name),
			(doc.get("quotation_to"), party.get("name") if party else None),
			("Opportunity", doc.get("opportunity")),
			*[("Sales Order", order_name) for order_name in sales_order_names],
		]
	)

	return {
		"summary": {
			"name": doc.name,
			"customer_label": doc.get("customer_name") or (party.get("name") if party else None) or doc.get("party_name"),
			"party_doctype": doc.get("quotation_to"),
			"party_name": party.get("name") if party else None,
			"status": doc.status,
			"workflow_state": doc.get("workflow_state"),
			"owner": doc.owner,
			"owner_display": _user_display(doc.owner),
			"transaction_date": str(doc.transaction_date) if doc.transaction_date else None,
			"valid_till": str(doc.valid_till) if doc.valid_till else None,
			"days_to_expiry": _days_until(doc.get("valid_till"), today),
			"validity_state": _quotation_validity_state(doc, today),
			"currency": doc.currency,
			"grand_total": float(doc.grand_total or 0),
			"order_type": doc.get("order_type"),
			"opportunity": doc.get("opportunity"),
			"sales_order_count": len(sales_order_names),
			"delivery_count": len(delivery_names),
			"invoice_count": len(invoice_names),
		},
		"linked_documents": {
			"party": party,
			"opportunity": opportunity,
			"sales_orders": _doc_rows("Sales Order", sales_order_names, ["name", "status", "transaction_date", "delivery_date"], "transaction_date asc, creation asc"),
			"deliveries": _doc_rows("Delivery Note", delivery_names, ["name", "status", "posting_date"]),
			"invoices": _doc_rows("Sales Invoice", invoice_names, ["name", "status", "posting_date", "outstanding_amount"]),
		},
		"support": {
			"latest_task": todos[0] if todos else None,
			"open_task_count": len(todos),
			"approval_note": _quotation_approval_note(doc),
			"customer_response_hint": _quotation_customer_response_hint(doc, sales_order_names, today),
			"commercial_note": _quotation_commercial_note(doc, sales_order_names, today),
			"next_action": _quotation_next_action(doc, sales_order_names, todos, today),
			"detail_guide": _quotation_detail_guide(doc),
		},
	}


@frappe.whitelist()
def get_delivery_note_page_context(name: str) -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	if not name:
		frappe.throw(_("Delivery Note is required"))

	doc = frappe.get_doc("Delivery Note", name)
	if not doc.has_permission("read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	sales_order_names = _linked_sales_order_names_from_delivery_note(doc.name)
	invoice_names = _linked_invoice_names_from_delivery_note(doc.name)
	return_names = _linked_return_delivery_names(doc.name)
	customer = _linked_doc("Customer", doc.get("customer"), ["name"])
	source_delivery = _linked_doc("Delivery Note", doc.get("return_against"), ["name", "status", "posting_date"])
	source_warehouse = _linked_doc("Warehouse", doc.get("set_warehouse"), ["name"])
	target_warehouse = _linked_doc("Warehouse", doc.get("set_target_warehouse"), ["name"])
	delivery_trip = _linked_doc("Delivery Trip", doc.get("delivery_trip"), ["name"])
	driver = _linked_doc("Driver", doc.get("driver"), ["name"])
	transporter = _linked_doc("Supplier", doc.get("transporter"), ["name"])
	todos = _linked_reference_todos(
		[
			("Delivery Note", doc.name),
			("Customer", doc.get("customer")),
			*[("Sales Order", order_name) for order_name in sales_order_names],
			*[("Sales Invoice", invoice_name) for invoice_name in invoice_names],
			*[("Delivery Note", return_name) for return_name in return_names],
			("Delivery Note", source_delivery.get("name") if source_delivery else None),
		]
	)

	return {
		"summary": {
			"name": doc.name,
			"customer": doc.get("customer"),
			"customer_label": doc.get("customer_name") or doc.get("customer"),
			"status": doc.status,
			"workflow_state": doc.get("workflow_state"),
			"owner": doc.owner,
			"owner_display": _user_display(doc.owner),
			"posting_date": str(doc.posting_date) if doc.posting_date else None,
			"posting_time": str(doc.posting_time) if doc.posting_time else None,
			"currency": doc.currency,
			"grand_total": float(doc.grand_total or 0),
			"total_qty": float(doc.total_qty or 0),
			"per_billed": float(doc.per_billed or 0),
			"per_returned": float(doc.per_returned or 0),
			"is_return": int(doc.is_return or 0),
			"return_against": doc.get("return_against"),
			"company": doc.get("company"),
			"set_warehouse": doc.get("set_warehouse"),
			"set_target_warehouse": doc.get("set_target_warehouse"),
			"transporter": doc.get("transporter"),
			"driver": doc.get("driver"),
			"vehicle_no": doc.get("vehicle_no"),
			"delivery_trip": doc.get("delivery_trip"),
			"sales_order_count": len(sales_order_names),
			"invoice_count": len(invoice_names),
			"return_count": len(return_names),
		},
		"linked_documents": {
			"customer": {"doctype": "Customer", **customer} if customer else None,
			"sales_orders": _doc_rows("Sales Order", sales_order_names, ["name", "status", "transaction_date", "delivery_date"], "transaction_date asc, creation asc"),
			"invoices": _doc_rows("Sales Invoice", invoice_names, ["name", "status", "posting_date", "outstanding_amount"]),
			"source_delivery": source_delivery,
			"returns": _doc_rows("Delivery Note", return_names, ["name", "status", "posting_date"], "posting_date desc, creation desc"),
			"source_warehouse": {"doctype": "Warehouse", **source_warehouse} if source_warehouse else None,
			"target_warehouse": {"doctype": "Warehouse", **target_warehouse} if target_warehouse else None,
			"delivery_trip": {"doctype": "Delivery Trip", **delivery_trip} if delivery_trip else None,
			"driver": {"doctype": "Driver", **driver} if driver else None,
			"transporter": {"doctype": "Supplier", **transporter} if transporter else None,
		},
		"support": {
			"latest_task": todos[0] if todos else None,
			"open_task_count": len(todos),
			"approval_note": _delivery_note_approval_note(doc),
			"fulfillment_note": _delivery_note_fulfillment_note(doc),
			"customer_response_hint": _delivery_note_customer_response_hint(doc, invoice_names),
			"next_action": _delivery_note_next_action(doc, invoice_names, return_names, todos),
			"detail_guide": _delivery_note_detail_guide(doc),
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


def _linked_doc(doctype: str | None, name: str | None, fields: list[str] | None = None) -> dict[str, object] | None:
	if not doctype or not name or not frappe.db.exists("DocType", doctype):
		return None
	field_list = list(dict.fromkeys((fields or ["name"]) + ["name"]))
	rows = frappe.get_list(doctype, filters={"name": name}, fields=field_list, limit_page_length=1)
	return rows[0] if rows else None


def _quotation_party_doc(doc) -> dict[str, object] | None:
	doctype = doc.get("quotation_to")
	if not doctype or not frappe.db.exists("DocType", doctype):
		return None

	for candidate in (doc.get("party_name"), doc.get("customer_name") if doctype == "Customer" else None):
		if not candidate:
			continue
		record = _linked_doc(doctype, candidate, ["name"])
		if record:
			return {"doctype": doctype, **record}
	return None


def _linked_sales_order_names_from_quotation(quotation: str) -> list[str]:
	if not quotation or not frappe.db.exists("DocType", "Sales Order Item"):
		return []
	parents = frappe.get_all(
		"Sales Order Item",
		filters={"prevdoc_docname": quotation},
		fields=["parent"],
		distinct=True,
		order_by="parent asc",
	)
	names = [row["parent"] for row in parents if row.get("parent")]
	if not names:
		return []
	visible = frappe.get_list(
		"Sales Order",
		filters={"name": ["in", names], "docstatus": ["!=", 2]},
		fields=["name"],
		order_by="transaction_date asc, creation asc",
		limit_page_length=200,
	)
	index = {row["name"]: row["name"] for row in visible}
	return [name for name in names if name in index]


def _linked_sales_order_names_from_delivery_note(delivery_note: str) -> list[str]:
	if not delivery_note or not frappe.db.exists("DocType", "Delivery Note Item"):
		return []
	rows = frappe.get_all(
		"Delivery Note Item",
		filters={"parent": delivery_note, "against_sales_order": ["is", "set"]},
		fields=["against_sales_order"],
		distinct=True,
		order_by="against_sales_order asc",
	)
	names = [row["against_sales_order"] for row in rows if row.get("against_sales_order")]
	if not names:
		return []
	visible = frappe.get_list(
		"Sales Order",
		filters={"name": ["in", names], "docstatus": ["!=", 2]},
		fields=["name"],
		order_by="transaction_date asc, creation asc",
		limit_page_length=200,
	)
	index = {row["name"]: row["name"] for row in visible}
	return [name for name in names if name in index]


def _linked_delivery_names_from_sales_orders(sales_orders: list[str]) -> list[str]:
	if not sales_orders or not frappe.db.exists("DocType", "Delivery Note Item"):
		return []
	parents = frappe.get_all(
		"Delivery Note Item",
		filters={"against_sales_order": ["in", sales_orders]},
		fields=["parent"],
		distinct=True,
		order_by="parent asc",
	)
	names = [row["parent"] for row in parents if row.get("parent")]
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


def _linked_invoice_names_from_delivery_note(delivery_note: str) -> list[str]:
	if not delivery_note or not frappe.db.exists("DocType", "Sales Invoice Item"):
		return []
	rows = frappe.get_all(
		"Sales Invoice Item",
		filters={"delivery_note": delivery_note},
		fields=["parent"],
		distinct=True,
		order_by="parent asc",
	)
	names = [row["parent"] for row in rows if row.get("parent")]
	if not names:
		return []
	visible = frappe.get_list(
		"Sales Invoice",
		filters={"name": ["in", names], "docstatus": ["!=", 2]},
		fields=["name"],
		order_by="posting_date asc, creation asc",
		limit_page_length=200,
	)
	index = {row["name"]: row["name"] for row in visible}
	return [name for name in names if name in index]


def _linked_return_delivery_names(delivery_note: str) -> list[str]:
	if not delivery_note:
		return []
	rows = frappe.get_list(
		"Delivery Note",
		filters={"is_return": 1, "return_against": delivery_note, "docstatus": ["!=", 2]},
		fields=["name"],
		order_by="posting_date desc, creation desc",
		limit_page_length=100,
	)
	return [row["name"] for row in rows if row.get("name")]


def _linked_invoice_names_from_sales_orders(sales_orders: list[str]) -> list[str]:
	if not sales_orders or not frappe.db.exists("DocType", "Sales Invoice Item"):
		return []
	parents = frappe.get_all(
		"Sales Invoice Item",
		filters={"sales_order": ["in", sales_orders]},
		fields=["parent"],
		distinct=True,
		order_by="parent asc",
	)
	names = [row["parent"] for row in parents if row.get("parent")]
	if not names:
		return []
	visible = frappe.get_list(
		"Sales Invoice",
		filters={"name": ["in", names], "docstatus": ["!=", 2], "is_return": ["!=", 1]},
		fields=["name"],
		order_by="posting_date asc, creation asc",
		limit_page_length=200,
	)
	index = {row["name"]: row["name"] for row in visible}
	return [name for name in names if name in index]


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


def _linked_reference_todos(reference_pairs: list[tuple[str | None, str | None]]) -> list[dict[str, object]]:
	valid_pairs = [(doctype, name) for doctype, name in reference_pairs if doctype and name]
	if not valid_pairs:
		return []
	return frappe.get_list(
		"ToDo",
		filters={
			"status": ["!=", "Closed"],
			"reference_name": ["in", sorted({name for _doctype, name in valid_pairs})],
			"reference_type": ["in", sorted({doctype for doctype, _name in valid_pairs})],
		},
		fields=["name", "description", "allocated_to", "date", "reference_type", "reference_name"],
		order_by="date asc, creation asc",
		limit_page_length=50,
	)


def _doc_rows(doctype: str, names: list[str], fields: list[str], order_by: str = "posting_date asc, creation asc") -> list[dict[str, object]]:
	if not names:
		return []
	ordered_names = list(dict.fromkeys(name for name in names if name))
	rows = frappe.get_list(
		doctype,
		filters={"name": ["in", ordered_names], "docstatus": ["!=", 2]},
		fields=fields,
		order_by=order_by,
		limit_page_length=100,
	)
	index = {row["name"]: row for row in rows}
	return [index[name] for name in ordered_names if name in index]


def _days_until(raw_date, today) -> int | None:
	if not raw_date:
		return None
	return (getdate(raw_date) - today).days


def _quotation_pending_states() -> set[str]:
	return {"Pending Sales Approval", "Pending Executive Approval"}


def _quotation_validity_state(doc, today) -> str:
	valid_till = getdate(doc.get("valid_till")) if doc.get("valid_till") else None
	status = str(doc.get("status") or "").strip()
	if not valid_till:
		return "no_valid_till"
	if status in {"Cancelled", "Lost", "Ordered"}:
		return "inactive"
	if valid_till < today:
		return "expired"
	if valid_till <= today + timedelta(days=7):
		return "expiring_soon"
	return "active"


def _quotation_approval_note(doc) -> str:
	workflow_state = str(doc.get("workflow_state") or "").strip()
	if workflow_state in _quotation_pending_states():
		reasons = []
		if float(doc.get("grand_total") or 0) >= 25000000:
			reasons.append("high quotation value")
		elif float(doc.get("grand_total") or 0) >= 10000000:
			reasons.append("manager approval threshold")
		if float(doc.get("additional_discount_percentage") or 0) > 0:
			reasons.append("additional discount")
		if float(doc.get("discount_amount") or 0) > 0:
			reasons.append("discount amount override")
		if reasons:
			return f"Approval is active because of {', '.join(reasons)}."
		return "Approval is active for this quotation and must be completed before normal commercial commitment."
	return "No active approval blocker is present on this quotation."


def _quotation_commercial_note(doc, sales_order_names: list[str], today) -> str:
	workflow_state = str(doc.get("workflow_state") or "").strip()
	valid_till = getdate(doc.get("valid_till")) if doc.get("valid_till") else None
	if sales_order_names:
		return "This quotation already has downstream sales-order activity and should be reviewed as part of the conversion chain."
	if valid_till and valid_till < today:
		return "This quotation is past validity and needs immediate commercial review before any further promise is made."
	if workflow_state in _quotation_pending_states():
		return "This quotation is commercially prepared and currently waiting on approval review."
	if valid_till and valid_till <= today + timedelta(days=3):
		return "Quotation validity is approaching soon and needs close customer follow-through."
	return "This quotation is active in the commercial pipeline and ready for customer follow-up."


def _quotation_customer_response_hint(doc, sales_order_names: list[str], today) -> str:
	workflow_state = str(doc.get("workflow_state") or "").strip()
	valid_till = getdate(doc.get("valid_till")) if doc.get("valid_till") else None
	if sales_order_names:
		return "Tell the customer the quotation is already moving into downstream order handling."
	if workflow_state in _quotation_pending_states():
		return "Tell the customer the quotation is under approval review before final confirmation can be given."
	if valid_till and valid_till < today:
		return "Tell the customer the quotation validity has lapsed and a revised commercial confirmation is required."
	if valid_till and valid_till <= today + timedelta(days=3):
		return "Tell the customer the quotation is still active but the validity window is approaching soon."
	return "Tell the customer the quotation is active and currently under normal commercial follow-through."


def _quotation_next_action(doc, sales_order_names: list[str], todos: list[dict[str, object]], today) -> str:
	workflow_state = str(doc.get("workflow_state") or "").strip()
	valid_till = getdate(doc.get("valid_till")) if doc.get("valid_till") else None
	if sales_order_names:
		return "Review the linked sales-order activity first and align the customer-facing handoff with the downstream order state."
	if workflow_state in _quotation_pending_states():
		return "Complete the active approval step before confirming commercial commitment to the customer."
	if todos:
		task = todos[0]
		task_desc = task.get("description") or task.get("name")
		return f"Work the current follow-up task first: {task_desc}."
	if valid_till and valid_till < today:
		return "Review pricing and customer intent now because this quotation is already outside its validity window."
	if valid_till and valid_till <= today + timedelta(days=3):
		return "Follow up with the customer now because the quotation validity window is approaching soon."
	return "Continue commercial follow-through and keep the next conversion step ready if the customer confirms."


def _quotation_detail_guide(doc) -> str:
	if doc.docstatus == 0:
		return "Use the detailed form sections below to refine items, pricing, terms, and validity before final commercial commitment."
	return "Use the detailed form sections below for precise quotation maintenance while keeping the commercial summary above as the main working guide."


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


def _delivery_note_approval_note(doc) -> str:
	workflow_state = str(doc.get("workflow_state") or "").strip()
	if workflow_state and "Pending" in workflow_state:
		return f"This delivery note is currently in workflow state {workflow_state} and should be reviewed before further changes."
	return "No active workflow blocker is present on this delivery note."


def _delivery_note_fulfillment_note(doc) -> str:
	status = str(doc.get("status") or "").strip()
	per_billed = float(doc.get("per_billed") or 0)
	per_returned = float(doc.get("per_returned") or 0)
	if int(doc.get("is_return") or 0):
		return "This document is a return delivery note and should be reviewed against the original delivery before further customer follow-through."
	if per_returned > 0:
		return "Some quantity has already moved into return handling and should stay visible during billing or customer follow-up."
	if status == "Partially Billed" or (per_billed > 0 and per_billed < 100):
		return "Delivery is already posted and billing is only partially complete."
	if status == "To Bill":
		return "Delivery is complete enough for billing follow-through and should be reviewed together with the invoice chain."
	if status == "Completed":
		return "This delivery note reads as operationally complete."
	return "This delivery note is part of the active fulfillment execution chain."


def _delivery_note_customer_response_hint(doc, invoice_names: list[str]) -> str:
	status = str(doc.get("status") or "").strip()
	per_billed = float(doc.get("per_billed") or 0)
	if int(doc.get("is_return") or 0):
		return "Tell the customer this record is handling a return against the original delivery and the reversal flow is being followed through."
	if invoice_names and per_billed >= 100:
		return "Tell the customer delivery and billing linkage are already complete for this document."
	if status == "Partially Billed" or (per_billed > 0 and per_billed < 100):
		return "Tell the customer delivery is posted and billing is still being completed."
	if status == "To Bill":
		return "Tell the customer the goods are delivered and the billing step is the main remaining follow-through."
	return "Tell the customer this delivery note is recorded in the normal fulfillment chain and linked documents are available for follow-up."


def _delivery_note_next_action(doc, invoice_names: list[str], return_names: list[str], todos: list[dict[str, object]]) -> str:
	workflow_state = str(doc.get("workflow_state") or "").strip()
	status = str(doc.get("status") or "").strip()
	per_billed = float(doc.get("per_billed") or 0)
	if workflow_state and "Pending" in workflow_state:
		return "Complete the active workflow step before making further delivery-side changes."
	if todos:
		task = todos[0]
		task_desc = task.get("description") or task.get("name")
		return f"Work the current follow-up task first: {task_desc}."
	if int(doc.get("is_return") or 0) and doc.get("return_against"):
		return "Review the source delivery first and align the return handling with the original fulfillment record."
	if return_names:
		return "Review the linked return activity first so the fulfillment chain stays aligned before more billing follow-through."
	if status in {"To Bill", "Partially Billed"} or per_billed < 100:
		return "Finish invoice follow-through now because the delivery is already posted but the billing chain is not closed yet."
	if invoice_names:
		return "Review the linked invoice documents first before making further customer-facing fulfillment statements."
	return "Continue normal fulfillment follow-through and use the linked order, invoice, and return context when customer questions arise."


def _delivery_note_detail_guide(doc) -> str:
	if doc.docstatus == 0:
		return "Use the detailed form sections below to complete items, addresses, and stock movement details before submitting the delivery note."
	return "Use the detailed form sections below for precise maintenance while keeping the fulfillment summary above as the main working guide."
