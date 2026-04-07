from __future__ import annotations

import datetime as dt
import re
from typing import Any, Dict, List, Optional, Tuple

import frappe

from ai_assistant_ui.qwen_chat.artifact_narrative import (
	build_artifact_narrative_context,
	build_artifact_narrative_contract,
	narrate_governed_artifact,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _normalize_text(value: Any) -> str:
	return " ".join(_clean_text(value).lower().split())


def _iso_date(value: Any) -> str:
	if isinstance(value, (dt.date, dt.datetime)):
		return value.isoformat()[:10]
	return _clean_text(value)


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _money(value: Any) -> str:
	return f"{_numeric(value):,.2f}".rstrip("0").rstrip(".")


def _markdown_table(columns: List[str], rows: List[List[str]]) -> str:
	if not columns or not rows:
		return ""
	lines = [
		"| " + " | ".join(columns) + " |",
		"| " + " | ".join("---" for _ in columns) + " |",
	]
	for row in rows:
		lines.append("| " + " | ".join(str(cell or "").strip() for cell in row) + " |")
	return "\n".join(lines).strip()


def _render_blocks_markdown(rendered_payload: Dict[str, Any]) -> str:
	blocks = rendered_payload.get("blocks") if isinstance(rendered_payload.get("blocks"), list) else []
	lines: List[str] = []
	title = _clean_text(rendered_payload.get("title"))
	if title:
		lines.append(f"## {title}")
	for block in blocks:
		if not isinstance(block, dict):
			continue
		block_title = _clean_text(block.get("title"))
		block_type = _clean_text(block.get("block_type"))
		if block_title:
			lines.append(f"### {block_title}")
		if block_type in {"summary_table", "data_table"}:
			columns = [_clean_text(col) for col in (block.get("columns") or []) if _clean_text(col)]
			rows = [
				[_clean_text(cell) for cell in row]
				for row in (block.get("rows") or [])
				if isinstance(row, list)
			]
			table = _markdown_table(columns, rows)
			if table:
				lines.append(table)
		elif block_type == "bullet_list":
			for item in (block.get("items") or []):
				value = _clean_text(item)
				if value:
					lines.append(f"- {value}")
	return "\n\n".join(part for part in lines if part).strip()


def _identifier_candidates(message: str) -> List[str]:
	return list(dict.fromkeys(re.findall(r"\b[A-Z0-9]{2,}(?:-[A-Z0-9]+){2,}\b", str(message or ""))))


def _explicit_detail_request(message: str) -> bool:
	text = _normalize_text(message)
	if _identifier_candidates(message):
		return True
	return any(
		phrase in text
		for phrase in (
			"give me details",
			"give me detail",
			"tell me more",
			"more information",
			"show details",
			"show detail",
			"history",
			"payment history",
			"purchase history",
			"previous purchases",
			"purchasing pattern",
		)
	)


def _resolve_item_name(name_or_code: str) -> Tuple[str, str]:
	value = _clean_text(name_or_code)
	if not value:
		return "", ""
	if frappe.db.exists("Item", value):
		item_name = _clean_text(frappe.db.get_value("Item", value, "item_name"))
		return value, item_name or value
	row = frappe.db.get_value("Item", {"item_name": value}, ["name", "item_name"], as_dict=True)
	if isinstance(row, dict):
		return _clean_text(row.get("name")), _clean_text(row.get("item_name")) or value
	return "", ""


def _resolve_explicit_identifier(message: str) -> Optional[Dict[str, Any]]:
	for candidate in _identifier_candidates(message):
		if frappe.db.exists("Sales Invoice", candidate):
			return {"entity_type": "sales_invoice", "entity_key": candidate, "entity_label": candidate, "source": "explicit_identifier"}
		if frappe.db.exists("Purchase Invoice", candidate):
			return {"entity_type": "purchase_invoice", "entity_key": candidate, "entity_label": candidate, "source": "explicit_identifier"}
		if frappe.db.exists("Delivery Note", candidate):
			return {"entity_type": "delivery_note", "entity_key": candidate, "entity_label": candidate, "source": "explicit_identifier"}
		item_code, item_name = _resolve_item_name(candidate)
		if item_code:
			return {"entity_type": "item", "entity_key": item_code, "entity_label": item_name or item_code, "source": "explicit_identifier"}
	return None


def _artifact_entity_candidates(artifact_payload: Dict[str, Any] | None) -> List[Dict[str, Any]]:
	artifact = dict(artifact_payload or {}) if isinstance(artifact_payload, dict) else {}
	sections = dict(artifact.get("sections") or {}) if isinstance(artifact.get("sections"), dict) else {}
	dimensions = dict(artifact.get("dimensions") or {}) if isinstance(artifact.get("dimensions"), dict) else {}
	family_id = _clean_text(artifact.get("family_id"))
	out: List[Dict[str, Any]] = []

	def _append(entity_type: str, entity_key: Any, entity_label: Any = "", *, alias: Any = "") -> None:
		key = _clean_text(entity_key)
		label = _clean_text(entity_label) or key
		if not key and not label:
			return
		payload = {
			"entity_type": _clean_text(entity_type),
			"entity_key": key or label,
			"entity_label": label or key,
			"alias": _clean_text(alias),
			"source": "artifact_context",
		}
		if payload not in out:
			out.append(payload)

	def _entity_type_from_dimension(value: str) -> str:
		dimension_keys = detect_canonical_keys(value, dimension_or_metric="dimension")
		for key in dimension_keys:
			if key == "supplier":
				return "supplier"
			if key == "customer":
				return "customer"
			if key in {"item_code", "item_name"}:
				return "item"
		return ""

	if family_id == "transaction_listing":
		document_entity_type = _clean_text(dimensions.get("document_entity_type") or dimensions.get("transaction_type")) or "sales_invoice"
		for row in sections.get("transaction_rows") or []:
			if not isinstance(row, dict):
				continue
			_append(document_entity_type, row.get("document_name"))
			_append("customer", row.get("customer") or row.get("party_name"))
	elif family_id == "aging":
		entity_type = "supplier" if _clean_text(dimensions.get("aging_type")) == "accounts_payable" else "customer"
		for row in sections.get("parties") or []:
			if not isinstance(row, dict):
				continue
			_append(entity_type, row.get("party"))
			_append("purchase_invoice" if entity_type == "supplier" else "sales_invoice", row.get("voucher_no"))
	elif family_id == "ranking_analytics":
		entity_type = _entity_type_from_dimension(_clean_text(dimensions.get("entity_dimension")))
		for row in sections.get("ranked_rows") or []:
			if not isinstance(row, dict):
				continue
			label = row.get("entity_name") or row.get("entity")
			key = row.get("entity_code") or row.get("entity") or row.get("entity_name")
			_append(entity_type, key, label)
	elif family_id == "product_profitability":
		for row in sections.get("product_rows") or []:
			if not isinstance(row, dict):
				continue
			_append("item", row.get("item_code") or row.get("item_name"), row.get("item_name") or row.get("item_code"))
	return out[:50]


def detect_entity_drilldown_request(
	*,
	message: str,
	artifact_payload: Dict[str, Any] | None,
	grounded_turn: Dict[str, Any] | None = None,
) -> Optional[Dict[str, Any]]:
	if not _explicit_detail_request(message):
		return None
	explicit = _resolve_explicit_identifier(message)
	if explicit:
		return explicit

	text = _normalize_text(message)
	for candidate in sorted(
		_artifact_entity_candidates(artifact_payload),
		key=lambda item: len(_clean_text(item.get("entity_label") or item.get("entity_key"))),
		reverse=True,
	):
		key = _normalize_text(candidate.get("entity_key"))
		label = _normalize_text(candidate.get("entity_label"))
		if key and key in text:
			return candidate
		if label and label in text:
			return candidate

	known_entities = grounded_turn.get("known_entities") if isinstance(grounded_turn, dict) else []
	if isinstance(known_entities, list):
		for item in sorted(
			[item for item in known_entities if isinstance(item, dict)],
			key=lambda value: len(_clean_text(value.get("name"))),
			reverse=True,
		):
			name = _normalize_text(item.get("name"))
			if name and name in text:
				return {
					"entity_type": _clean_text(item.get("entity_type")),
					"entity_key": _clean_text(item.get("code") or item.get("name")),
					"entity_label": _clean_text(item.get("name")),
					"source": "grounded_turn",
				}
	return None


def _summary_block(title: str, rows: List[Tuple[str, Any]]) -> Dict[str, Any]:
	return {
		"block_type": "summary_table",
		"title": title,
		"columns": ["Field", "Value"],
		"rows": [[_clean_text(label), _clean_text(value)] for label, value in rows if _clean_text(label) and _clean_text(value)],
	}


def _data_block(title: str, columns: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
	return {
		"block_type": "data_table",
		"title": title,
		"columns": [_clean_text(col) for col in columns if _clean_text(col)],
		"rows": [[_clean_text(cell) for cell in row] for row in rows if isinstance(row, list)],
	}


def _bullet_block(title: str, items: List[str]) -> Dict[str, Any]:
	return {
		"block_type": "bullet_list",
		"title": title,
		"items": [_clean_text(item) for item in items if _clean_text(item)],
	}


def _sales_invoice_delivery_proof(doc) -> Dict[str, Any]:
	items = list(doc.get("items") or [])
	is_return = int(getattr(doc, "is_return", 0) or 0)
	update_stock = int(getattr(doc, "update_stock", 0) or 0)
	item_count = len(items)
	linked_sales_orders = sorted(
		{
			_clean_text(getattr(row, "sales_order", ""))
			for row in items
			if _clean_text(getattr(row, "sales_order", ""))
		}
	)
	linked_delivery_note_names = sorted(
		{
			_clean_text(getattr(row, "delivery_note", ""))
			for row in items
			if _clean_text(getattr(row, "delivery_note", "")) and _clean_text(getattr(row, "dn_detail", ""))
		}
	)
	delivery_note_rows: List[Dict[str, Any]] = []
	submitted_delivery_note_names: List[str] = []
	for delivery_note_name in linked_delivery_note_names:
		row = frappe.db.get_value(
			"Delivery Note",
			delivery_note_name,
			["name", "docstatus", "status", "posting_date", "is_return", "return_against"],
			as_dict=True,
		)
		row_payload = dict(row or {}) if isinstance(row, dict) else {}
		row_docstatus = int(row_payload.get("docstatus") or 0)
		delivery_note_rows.append(
			{
				"delivery_note": delivery_note_name,
				"docstatus": row_docstatus,
				"status": _clean_text(row_payload.get("status")),
				"posting_date": _iso_date(row_payload.get("posting_date")),
				"is_return": int(row_payload.get("is_return") or 0),
				"return_against": _clean_text(row_payload.get("return_against")),
			}
		)
		if row_docstatus == 1:
			submitted_delivery_note_names.append(delivery_note_name)
	submitted_delivery_note_names = sorted(dict.fromkeys(submitted_delivery_note_names))
	submitted_linked_item_count = 0
	for row in items:
		delivery_note_name = _clean_text(getattr(row, "delivery_note", ""))
		dn_detail = _clean_text(getattr(row, "dn_detail", ""))
		if delivery_note_name and dn_detail and delivery_note_name in submitted_delivery_note_names:
			submitted_linked_item_count += 1
	proof_state = "insufficient_governed_delivery_evidence"
	proof_method = ""
	if update_stock:
		proof_state = (
			"direct_return_proven_via_invoice_stock"
			if is_return
			else "direct_delivery_proven_via_invoice_stock"
		)
		proof_method = "invoice_stock"
	elif item_count > 0 and submitted_linked_item_count == item_count:
		proof_state = (
			"direct_return_proven_via_linked_delivery_note"
			if is_return
			else "direct_delivery_proven_via_linked_delivery_note"
		)
		proof_method = "linked_delivery_note"
	return {
		"proof_state": proof_state,
		"proof_method": proof_method,
		"is_return": is_return,
		"update_stock": update_stock,
		"item_count": item_count,
		"submitted_linked_item_count": submitted_linked_item_count,
		"linked_delivery_note_count": len(submitted_delivery_note_names),
		"delivery_notes": delivery_note_rows,
		"submitted_delivery_notes": submitted_delivery_note_names,
		"submitted_delivery_dates": sorted(
			{
				str(row.get("posting_date") or "").strip()
				for row in delivery_note_rows
				if int(row.get("docstatus") or 0) == 1 and str(row.get("posting_date") or "").strip()
			}
		),
		"sales_orders": linked_sales_orders,
	}


def _sales_invoice_detail(entity_key: str) -> Dict[str, Any]:
	doc = frappe.get_doc("Sales Invoice", entity_key)
	delivery_proof = _sales_invoice_delivery_proof(doc)
	item_rows = [
		[
			_clean_text(row.item_code),
			_clean_text(row.item_name),
			_clean_text(row.qty),
			_money(row.net_amount or row.amount or 0),
		]
		for row in (doc.get("items") or [])[:10]
	]
	summary = [
		("Invoice", doc.name),
		("Posting Date", _iso_date(doc.posting_date)),
		("Customer", _clean_text(doc.customer)),
		("Status", _clean_text(doc.status)),
		("Due Date", _iso_date(doc.due_date)),
		("Grand Total (MMK)", _money(doc.grand_total)),
		("Outstanding (MMK)", _money(doc.outstanding_amount)),
		("Company", _clean_text(doc.company)),
	]
	bullets = []
	if _numeric(doc.outstanding_amount) > 0:
		bullets.append(f"Outstanding balance remains {_money(doc.outstanding_amount)} MMK.")
	if _clean_text(doc.status):
		bullets.append(f"Current invoice status is {_clean_text(doc.status)}.")
	if delivery_proof.get("proof_state") == "direct_delivery_proven_via_invoice_stock":
		bullets.append("This submitted invoice posted stock movement directly, which provides governed delivery proof.")
	elif delivery_proof.get("proof_state") == "direct_delivery_proven_via_linked_delivery_note":
		submitted_delivery_notes = list(delivery_proof.get("submitted_delivery_notes") or [])
		if submitted_delivery_notes:
			bullets.append(
				"All invoice items are linked to submitted delivery note(s): "
				+ ", ".join(submitted_delivery_notes[:3])
				+ ("." if len(submitted_delivery_notes) <= 3 else ", ...")
			)
	elif delivery_proof.get("proof_state") == "direct_return_proven_via_invoice_stock":
		bullets.append("This is a return invoice with direct stock reversal posted on the submitted invoice.")
	elif delivery_proof.get("proof_state") == "direct_return_proven_via_linked_delivery_note":
		submitted_delivery_notes = list(delivery_proof.get("submitted_delivery_notes") or [])
		if submitted_delivery_notes:
			bullets.append(
				"This return invoice is linked to submitted delivery note reversal evidence: "
				+ ", ".join(submitted_delivery_notes[:3])
				+ ("." if len(submitted_delivery_notes) <= 3 else ", ...")
			)
	rendered = {
		"type": "qwen_entity_detail_rendered_response",
		"request_id": "",
		"family_id": "entity_detail",
		"title": f"Sales Invoice {doc.name}",
		"source_reports": ["Sales Invoice"],
		"blocks": [
			_summary_block("Invoice Summary", summary),
			_bullet_block("Key Facts", bullets),
			_data_block("Items", ["Item Code", "Item Name", "Qty", "Amount (MMK)"], item_rows),
		],
	}
	artifact = {
		"type": "qwen_entity_detail_artifact",
		"artifact_type": "entity_detail_artifact",
		"family_id": "entity_detail",
		"source_reports": ["Sales Invoice"],
		"filters": {"company": _clean_text(doc.company), "entity_key": doc.name},
		"dimensions": {
			"entity_type": "sales_invoice",
			"entity_key": doc.name,
			"entity_label": doc.name,
			"primary_metric_key": "grand_total",
			"primary_metric_label": "Grand Total",
			"source_grain": "document_detail",
		},
		"metrics": {
			"grand_total": _numeric(doc.grand_total),
			"outstanding_amount": _numeric(doc.outstanding_amount),
			"item_count": len(item_rows),
			"linked_delivery_note_count": int(delivery_proof.get("linked_delivery_note_count") or 0),
		},
		"sections": {
			"summary": [{"label": label, "value": value} for label, value in summary if _clean_text(value)],
			"document_rows": [
				{
					"document_name": doc.name,
					"posting_date": _iso_date(doc.posting_date),
					"customer": _clean_text(doc.customer),
					"grand_total": _numeric(doc.grand_total),
					"outstanding_amount": _numeric(doc.outstanding_amount),
					"status": _clean_text(doc.status),
					"is_return": int(getattr(doc, "is_return", 0) or 0),
					"update_stock": int(getattr(doc, "update_stock", 0) or 0),
				}
			],
			"item_rows": [
				{
					"item_code": _clean_text(row.item_code),
					"item_name": _clean_text(row.item_name),
					"qty": _numeric(row.qty),
					"amount": _numeric(row.net_amount or row.amount or 0),
					"delivery_note": _clean_text(getattr(row, "delivery_note", "")),
					"dn_detail": _clean_text(getattr(row, "dn_detail", "")),
					"sales_order": _clean_text(getattr(row, "sales_order", "")),
				}
				for row in (doc.get("items") or [])[:25]
			],
			"delivery_proof": [delivery_proof],
		},
	}
	return {"artifact": artifact, "rendered": rendered, "company": _clean_text(doc.company), "entity_label": doc.name}


def _purchase_invoice_detail(entity_key: str) -> Dict[str, Any]:
	doc = frappe.get_doc("Purchase Invoice", entity_key)
	item_rows = [
		[
			_clean_text(row.item_code),
			_clean_text(row.item_name),
			_clean_text(row.qty),
			_money(row.amount or row.base_amount or 0),
		]
		for row in (doc.get("items") or [])[:10]
	]
	summary = [
		("Invoice", doc.name),
		("Posting Date", _iso_date(doc.posting_date)),
		("Supplier", _clean_text(doc.supplier)),
		("Status", _clean_text(doc.status)),
		("Due Date", _iso_date(doc.due_date)),
		("Grand Total (MMK)", _money(doc.grand_total)),
		("Outstanding (MMK)", _money(doc.outstanding_amount)),
		("Company", _clean_text(doc.company)),
	]
	bullets = []
	if _numeric(doc.outstanding_amount) > 0:
		bullets.append(f"Outstanding supplier balance remains {_money(doc.outstanding_amount)} MMK.")
	if _clean_text(doc.status):
		bullets.append(f"Current purchase invoice status is {_clean_text(doc.status)}.")
	rendered = {
		"type": "qwen_entity_detail_rendered_response",
		"request_id": "",
		"family_id": "entity_detail",
		"title": f"Purchase Invoice {doc.name}",
		"source_reports": ["Purchase Invoice"],
		"blocks": [
			_summary_block("Invoice Summary", summary),
			_bullet_block("Key Facts", bullets),
			_data_block("Items", ["Item Code", "Item Name", "Qty", "Amount (MMK)"], item_rows),
		],
	}
	artifact = {
		"type": "qwen_entity_detail_artifact",
		"artifact_type": "entity_detail_artifact",
		"family_id": "entity_detail",
		"source_reports": ["Purchase Invoice"],
		"filters": {"company": _clean_text(doc.company), "entity_key": doc.name},
		"dimensions": {
			"entity_type": "purchase_invoice",
			"entity_key": doc.name,
			"entity_label": doc.name,
			"primary_metric_key": "grand_total",
			"primary_metric_label": "Grand Total",
			"source_grain": "document_detail",
		},
		"metrics": {
			"grand_total": _numeric(doc.grand_total),
			"outstanding_amount": _numeric(doc.outstanding_amount),
			"item_count": len(item_rows),
		},
		"sections": {
			"summary": [{"label": label, "value": value} for label, value in summary if _clean_text(value)],
			"document_rows": [
				{
					"document_name": doc.name,
					"posting_date": _iso_date(doc.posting_date),
					"supplier": _clean_text(doc.supplier),
					"grand_total": _numeric(doc.grand_total),
					"outstanding_amount": _numeric(doc.outstanding_amount),
					"status": _clean_text(doc.status),
				}
			],
			"item_rows": [
				{
					"item_code": _clean_text(row.item_code),
					"item_name": _clean_text(row.item_name),
					"qty": _numeric(row.qty),
					"amount": _numeric(row.amount or row.base_amount or 0),
				}
				for row in (doc.get("items") or [])[:25]
			],
		},
	}
	return {"artifact": artifact, "rendered": rendered, "company": _clean_text(doc.company), "entity_label": doc.name}


def _delivery_note_detail(entity_key: str) -> Dict[str, Any]:
	doc = frappe.get_doc("Delivery Note", entity_key)
	item_rows = [
		[
			_clean_text(row.item_code),
			_clean_text(row.item_name),
			_clean_text(row.qty),
			_money(row.net_amount or row.amount or 0),
		]
		for row in (doc.get("items") or [])[:10]
	]
	linked_sales_orders = sorted(
		{
			_clean_text(row.against_sales_order)
			for row in (doc.get("items") or [])
			if _clean_text(row.against_sales_order)
		}
	)
	summary = [
		("Delivery Note", doc.name),
		("Posting Date", _iso_date(doc.posting_date)),
		("Customer", _clean_text(doc.customer)),
		("Status", _clean_text(doc.status)),
		("Return Against", _clean_text(getattr(doc, "return_against", ""))),
		("Total Quantity", _clean_text(getattr(doc, "total_qty", ""))),
		("Grand Total (MMK)", _money(doc.grand_total)),
		("Delivery Trip", _clean_text(getattr(doc, "delivery_trip", ""))),
		("Company", _clean_text(doc.company)),
	]
	bullets = []
	if int(getattr(doc, "is_return", 0) or 0):
		return_against = _clean_text(getattr(doc, "return_against", ""))
		if return_against:
			bullets.append(f"This delivery note is a return against {return_against}.")
		else:
			bullets.append("This delivery note is recorded as a return.")
	if _clean_text(doc.status):
		bullets.append(f"Current delivery note status is {_clean_text(doc.status)}.")
	if _numeric(getattr(doc, "per_billed", 0)) > 0:
		bullets.append(f"Billing completion is {_money(getattr(doc, 'per_billed', 0))}%.")
	if linked_sales_orders:
		bullets.append(f"Linked sales order reference starts from {linked_sales_orders[0]}.")
	rendered = {
		"type": "qwen_entity_detail_rendered_response",
		"request_id": "",
		"family_id": "entity_detail",
		"title": f"Delivery Note {doc.name}",
		"source_reports": ["Delivery Note"],
		"blocks": [
			_summary_block("Delivery Summary", summary),
			_bullet_block("Key Facts", bullets),
			_data_block("Items", ["Item Code", "Item Name", "Qty", "Amount (MMK)"], item_rows),
		],
	}
	artifact = {
		"type": "qwen_entity_detail_artifact",
		"artifact_type": "entity_detail_artifact",
		"family_id": "entity_detail",
		"source_reports": ["Delivery Note"],
		"filters": {"company": _clean_text(doc.company), "entity_key": doc.name},
		"dimensions": {
			"entity_type": "delivery_note",
			"entity_key": doc.name,
			"entity_label": doc.name,
			"primary_metric_key": "grand_total",
			"primary_metric_label": "Grand Total",
			"source_grain": "document_detail",
		},
		"metrics": {
			"grand_total": _numeric(doc.grand_total),
			"quantity": _numeric(getattr(doc, "total_qty", 0)),
			"item_count": len(item_rows),
		},
		"sections": {
			"summary": [{"label": label, "value": value} for label, value in summary if _clean_text(value)],
			"document_rows": [
				{
					"document_name": doc.name,
					"posting_date": _iso_date(doc.posting_date),
					"customer": _clean_text(doc.customer),
					"grand_total": _numeric(doc.grand_total),
					"quantity": _numeric(getattr(doc, "total_qty", 0)),
					"status": _clean_text(doc.status),
					"is_return": int(getattr(doc, "is_return", 0) or 0),
					"return_against": _clean_text(getattr(doc, "return_against", "")),
				}
			],
			"item_rows": [
				{
					"item_code": _clean_text(row.item_code),
					"item_name": _clean_text(row.item_name),
					"qty": _numeric(row.qty),
					"amount": _numeric(row.net_amount or row.amount or 0),
					"against_sales_order": _clean_text(row.against_sales_order),
				}
				for row in (doc.get("items") or [])[:25]
			],
		},
	}
	return {"artifact": artifact, "rendered": rendered, "company": _clean_text(doc.company), "entity_label": doc.name}


def _aggregate_invoice_stats(doctype: str, party_field: str, party_value: str, company: str) -> Dict[str, Any]:
	conditions = [f"{party_field}=%s", "docstatus=1"]
	values: List[Any] = [party_value]
	if company:
		conditions.append("company=%s")
		values.append(company)
	row = frappe.db.sql(
		f"""
		select count(*) as invoice_count,
		       coalesce(sum(grand_total), 0) as total_amount,
		       coalesce(sum(outstanding_amount), 0) as outstanding_amount,
		       max(posting_date) as latest_date,
		       min(posting_date) as first_date
		from `tab{doctype}`
		where {' and '.join(conditions)}
		""",
		tuple(values),
		as_dict=True,
	)
	return dict(row[0] or {}) if row else {}


def _recent_invoices(doctype: str, party_field: str, party_value: str, company: str) -> List[Dict[str, Any]]:
	filters = {party_field: party_value, "docstatus": 1}
	if company:
		filters["company"] = company
	return frappe.get_all(
		doctype,
		fields=["name", "posting_date", "grand_total", "outstanding_amount", "status"],
		filters=filters,
		order_by="posting_date desc",
		limit_page_length=7,
	)


def _customer_or_supplier_detail(entity_type: str, entity_key: str, company: str = "") -> Dict[str, Any]:
	doctype = "Customer" if entity_type == "customer" else "Supplier"
	invoice_doctype = "Sales Invoice" if entity_type == "customer" else "Purchase Invoice"
	party_field = "customer" if entity_type == "customer" else "supplier"
	name_field = "customer_name" if entity_type == "customer" else "supplier_name"
	group_field = "customer_group" if entity_type == "customer" else "supplier_group"
	territory_field = "territory" if entity_type == "customer" else "country"
	master = frappe.db.get_value(
		doctype,
		entity_key,
		["name", name_field, group_field, territory_field, "mobile_no", "email_id"],
		as_dict=True,
	)
	if not isinstance(master, dict):
		master = frappe.db.get_value(doctype, {name_field: entity_key}, ["name", name_field, group_field, territory_field, "mobile_no", "email_id"], as_dict=True) or {}
	entity_name = _clean_text(master.get("name")) or entity_key
	entity_label = _clean_text(master.get(name_field)) or entity_name
	stats = _aggregate_invoice_stats(invoice_doctype, party_field, entity_name, company)
	recent = _recent_invoices(invoice_doctype, party_field, entity_name, company)
	summary = [
		("Name", entity_label),
		("Code", entity_name),
		("Group", _clean_text(master.get(group_field))),
		("Territory / Region", _clean_text(master.get(territory_field))),
		("Mobile", _clean_text(master.get("mobile_no"))),
		("Email", _clean_text(master.get("email_id"))),
		("Invoice Count", int(stats.get("invoice_count") or 0)),
		("Total Amount (MMK)", _money(stats.get("total_amount"))),
		("Outstanding (MMK)", _money(stats.get("outstanding_amount"))),
		("Latest Invoice Date", _iso_date(stats.get("latest_date"))),
	]
	bullets = []
	if int(stats.get("invoice_count") or 0) > 0:
		bullets.append(f"{entity_label} has {int(stats.get('invoice_count') or 0)} posted {invoice_doctype.lower()} records in the governed history.")
	if _numeric(stats.get("outstanding_amount")) > 0:
		bullets.append(f"Current outstanding balance is {_money(stats.get('outstanding_amount'))} MMK.")
	if _clean_text(stats.get("latest_date")):
		bullets.append(f"Most recent governed transaction was on {_iso_date(stats.get('latest_date'))}.")
	recent_rows = [
		[
			_clean_text(row.get("name")),
			_iso_date(row.get("posting_date")),
			_money(row.get("grand_total")),
			_money(row.get("outstanding_amount")),
			_clean_text(row.get("status")),
		]
		for row in recent
	]
	rendered = {
		"type": "qwen_entity_detail_rendered_response",
		"request_id": "",
		"family_id": "entity_detail",
		"title": f"{entity_label} Details",
		"source_reports": [doctype, invoice_doctype],
		"blocks": [
			_summary_block("Profile", summary),
			_bullet_block("Highlights", bullets),
			_data_block(f"Recent {invoice_doctype}s", ["Invoice", "Posting Date", "Amount (MMK)", "Outstanding (MMK)", "Status"], recent_rows),
		],
	}
	artifact = {
		"type": "qwen_entity_detail_artifact",
		"artifact_type": "entity_detail_artifact",
		"family_id": "entity_detail",
		"source_reports": [doctype, invoice_doctype],
		"filters": {"company": company, "entity_key": entity_name},
		"dimensions": {
			"entity_type": entity_type,
			"entity_key": entity_name,
			"entity_label": entity_label,
			"primary_metric_key": "total_amount",
			"primary_metric_label": "Total Amount",
			"source_grain": "party_detail",
		},
		"metrics": {
			"invoice_count": int(stats.get("invoice_count") or 0),
			"total_amount": _numeric(stats.get("total_amount")),
			"outstanding_amount": _numeric(stats.get("outstanding_amount")),
		},
		"sections": {
			"summary": [{"label": label, "value": value} for label, value in summary if _clean_text(value)],
			"recent_transactions": [
				{
					"document_name": _clean_text(row.get("name")),
					"posting_date": _iso_date(row.get("posting_date")),
					"amount": _numeric(row.get("grand_total")),
					"outstanding_amount": _numeric(row.get("outstanding_amount")),
					"status": _clean_text(row.get("status")),
				}
				for row in recent
			],
		},
	}
	return {"artifact": artifact, "rendered": rendered, "company": company, "entity_label": entity_label}


def _item_detail(entity_key: str, company: str = "") -> Dict[str, Any]:
	item_code, item_name = _resolve_item_name(entity_key)
	if not item_code:
		raise frappe.DoesNotExistError(f"Item `{entity_key}` not found.")
	master = frappe.db.get_value(
		"Item",
		item_code,
		["name", "item_name", "item_group", "brand", "stock_uom", "disabled"],
		as_dict=True,
	) or {}
	conditions = ["sii.item_code=%s", "si.docstatus=1"]
	values: List[Any] = [item_code]
	if company:
		conditions.append("si.company=%s")
		values.append(company)
	stats_row = frappe.db.sql(
		f"""
		select count(distinct si.name) as invoice_count,
		       coalesce(sum(sii.qty), 0) as total_qty,
		       coalesce(sum(sii.net_amount), 0) as total_amount,
		       max(si.posting_date) as latest_date
		from `tabSales Invoice Item` sii
		inner join `tabSales Invoice` si on si.name = sii.parent
		where {' and '.join(conditions)}
		""",
		tuple(values),
		as_dict=True,
	)
	stats = dict(stats_row[0] or {}) if stats_row else {}
	recent = frappe.db.sql(
		f"""
		select si.name as invoice,
		       si.posting_date as posting_date,
		       sii.qty as qty,
		       sii.net_amount as amount
		from `tabSales Invoice Item` sii
		inner join `tabSales Invoice` si on si.name = sii.parent
		where {' and '.join(conditions)}
		order by si.posting_date desc
		limit 7
		""",
		tuple(values),
		as_dict=True,
	)
	entity_label = _clean_text(master.get("item_name")) or item_name or item_code
	summary = [
		("Item Name", entity_label),
		("Item Code", item_code),
		("Item Group", _clean_text(master.get("item_group"))),
		("Brand", _clean_text(master.get("brand"))),
		("UOM", _clean_text(master.get("stock_uom"))),
		("Disabled", "Yes" if master.get("disabled") else "No"),
		("Invoice Count", int(stats.get("invoice_count") or 0)),
		("Total Sold Qty", _clean_text(stats.get("total_qty"))),
		("Total Sales Amount (MMK)", _money(stats.get("total_amount"))),
		("Latest Sale Date", _iso_date(stats.get("latest_date"))),
	]
	bullets = []
	if int(stats.get("invoice_count") or 0) > 0:
		bullets.append(f"{entity_label} appears on {int(stats.get('invoice_count') or 0)} posted sales invoices in the governed history.")
	if _clean_text(stats.get("latest_date")):
		bullets.append(f"Most recent sale was on {_iso_date(stats.get('latest_date'))}.")
	recent_rows = [
		[
			_clean_text(row.get("invoice")),
			_iso_date(row.get("posting_date")),
			_clean_text(row.get("qty")),
			_money(row.get("amount")),
		]
		for row in recent
	]
	rendered = {
		"type": "qwen_entity_detail_rendered_response",
		"request_id": "",
		"family_id": "entity_detail",
		"title": f"{entity_label} Details",
		"source_reports": ["Item", "Sales Invoice Item"],
		"blocks": [
			_summary_block("Item Profile", summary),
			_bullet_block("Highlights", bullets),
			_data_block("Recent Sales", ["Invoice", "Posting Date", "Qty", "Amount (MMK)"], recent_rows),
		],
	}
	artifact = {
		"type": "qwen_entity_detail_artifact",
		"artifact_type": "entity_detail_artifact",
		"family_id": "entity_detail",
		"source_reports": ["Item", "Sales Invoice Item"],
		"filters": {"company": company, "entity_key": item_code},
		"dimensions": {
			"entity_type": "item",
			"entity_key": item_code,
			"entity_label": entity_label,
			"primary_metric_key": "total_amount",
			"primary_metric_label": "Total Sales Amount",
			"source_grain": "item_detail",
		},
		"metrics": {
			"invoice_count": int(stats.get("invoice_count") or 0),
			"total_qty": _numeric(stats.get("total_qty")),
			"total_amount": _numeric(stats.get("total_amount")),
		},
		"sections": {
			"summary": [{"label": label, "value": value} for label, value in summary if _clean_text(value)],
			"recent_transactions": [
				{
					"document_name": _clean_text(row.get("invoice")),
					"posting_date": _iso_date(row.get("posting_date")),
					"quantity": _numeric(row.get("qty")),
					"amount": _numeric(row.get("amount")),
				}
				for row in recent
			],
		},
	}
	return {"artifact": artifact, "rendered": rendered, "company": company, "entity_label": entity_label}


def _entity_grounded_turn_payload(
	*,
	request_id: str,
	entity_type: str,
	entity_key: str,
	entity_label: str,
	company: str,
	artifact_payload: Dict[str, Any],
) -> Dict[str, Any]:
	sections = dict(artifact_payload.get("sections") or {}) if isinstance(artifact_payload.get("sections"), dict) else {}
	recent_rows = sections.get("recent_transactions") if isinstance(sections.get("recent_transactions"), list) else []
	document_rows = sections.get("document_rows") if isinstance(sections.get("document_rows"), list) else []
	table_rows = recent_rows or document_rows
	if table_rows and isinstance(table_rows[0], dict):
		headers = [str(key or "").strip().replace("_", " ").title() for key in table_rows[0].keys()]
	else:
		headers = []
	return {
		"type": "qwen_grounded_turn_context",
		"contract_version": "1.0",
		"request_id": request_id,
		"trace_request_id": request_id,
		"grounded": True,
		"source_kind": "entity_detail",
		"source_name": f"{entity_label} Detail",
		"company": company,
		"date_range": {},
		"filters": {"company": company, "entity_type": entity_type, "entity_key": entity_key},
		"dimensions": [entity_type],
		"metrics": [str(key or "").strip() for key in (artifact_payload.get("metrics") or {}).keys()],
		"returned_schema": headers,
		"table_rows": list(table_rows or [])[:100],
		"row_count": len(table_rows or []),
		"base_language": "en",
		"transform_chain": [],
		"artifact_family_id": "entity_detail",
		"artifact_type": "entity_detail_artifact",
		"artifact_source_reports": [str(item or "").strip() for item in (artifact_payload.get("source_reports") or []) if _clean_text(item)],
		"known_entities": [{"entity_type": entity_type, "name": entity_label, "code": entity_key}],
		"known_documents": [
			str(row.get("document_name") or "").strip()
			for row in list(table_rows or [])
			if isinstance(row, dict) and str(row.get("document_name") or "").strip()
		],
	}


def execute_entity_drilldown(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	entity_reference: Dict[str, Any],
	response_policy: Dict[str, Any],
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	entity_type = _clean_text(entity_reference.get("entity_type"))
	entity_key = _clean_text(entity_reference.get("entity_key") or entity_reference.get("entity_label"))
	company = _clean_text((grounded_turn or {}).get("company")) if isinstance(grounded_turn, dict) else ""

	if entity_type == "sales_invoice":
		detail = _sales_invoice_detail(entity_key)
	elif entity_type == "purchase_invoice":
		detail = _purchase_invoice_detail(entity_key)
	elif entity_type == "delivery_note":
		detail = _delivery_note_detail(entity_key)
	elif entity_type == "customer":
		detail = _customer_or_supplier_detail("customer", entity_key, company=company)
	elif entity_type == "supplier":
		detail = _customer_or_supplier_detail("supplier", entity_key, company=company)
	elif entity_type == "item":
		detail = _item_detail(entity_key, company=company)
	else:
		raise frappe.ValidationError(f"Unsupported governed entity detail type `{entity_type}`.")

	artifact_payload = dict(detail.get("artifact") or {})
	rendered_payload = dict(detail.get("rendered") or {})
	artifact_payload["request_id"] = request_id
	rendered_payload["request_id"] = request_id
	entity_label = _clean_text(detail.get("entity_label")) or entity_key
	company = _clean_text(detail.get("company")) or company
	artifact_context = build_artifact_narrative_context(
		request_id=request_id,
		artifact_payload=artifact_payload,
		rendered_response_payload=rendered_payload,
		response_policy=response_policy,
		validation_payload={},
	)
	narrative_payload = narrate_governed_artifact(
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		request_id=request_id,
		artifact_context=artifact_context,
		response_policy=response_policy,
	)
	narrative_contract = build_artifact_narrative_contract(
		request_id=request_id,
		artifact_context=artifact_context,
		runtime_payload=narrative_payload,
	)
	answer_text = _clean_text((narrative_contract.to_payload() if narrative_contract else {}).get("answer_text"))
	if not answer_text:
		answer_text = _render_blocks_markdown(rendered_payload)
	if entity_label and _normalize_text(entity_label) not in _normalize_text(answer_text):
		prefix = f"Here are the details for {entity_label}."
		answer_text = f"{prefix}\n\n{answer_text}".strip() if answer_text else prefix
	return {
		"ok": bool(answer_text),
		"answer_text": answer_text,
		"artifact_payload": artifact_payload,
		"rendered_response_payload": rendered_payload,
		"narrative_payload": narrative_payload,
		"narrative_contract_payload": narrative_contract.to_payload() if narrative_contract is not None else {},
		"entity_reference": {
			"entity_type": entity_type,
			"entity_key": entity_key,
			"entity_label": entity_label,
		},
		"grounded_turn_payload": _entity_grounded_turn_payload(
			request_id=request_id,
			entity_type=entity_type,
			entity_key=entity_key,
			entity_label=entity_label,
			company=company,
			artifact_payload=artifact_payload,
		),
	}
