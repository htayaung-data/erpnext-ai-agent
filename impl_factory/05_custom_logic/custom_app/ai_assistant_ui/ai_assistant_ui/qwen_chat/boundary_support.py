from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.metadata import ontology_concept_aliases, ontology_detect_concepts
from ai_assistant_ui.qwen_chat.observability import (
	record_phase6_observability_event,
	record_phase6_performance_metric,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys, get_canonical_key, get_metric_label


def _artifact_delivery_proof(artifact_payload: Dict[str, Any]) -> Dict[str, Any]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	delivery_proof_rows = sections.get("delivery_proof") if isinstance(sections.get("delivery_proof"), list) else []
	if not delivery_proof_rows:
		return {}
	row = delivery_proof_rows[0]
	return dict(row or {}) if isinstance(row, dict) else {}


def _artifact_document_row(artifact_payload: Dict[str, Any]) -> Dict[str, Any]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	document_rows = sections.get("document_rows") if isinstance(sections.get("document_rows"), list) else []
	if not document_rows:
		return {}
	row = document_rows[0]
	return dict(row or {}) if isinstance(row, dict) else {}


def _artifact_item_rows(artifact_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	item_rows = sections.get("item_rows") if isinstance(sections.get("item_rows"), list) else []
	return [dict(row or {}) for row in item_rows if isinstance(row, dict)]


def _delivery_subject_phrase(item_rows: List[Dict[str, Any]]) -> str:
	if len(item_rows) == 1:
		row = item_rows[0]
		item_name = str(row.get("item_name") or row.get("item_code") or "the item").strip()
		qty = row.get("qty")
		if qty not in (None, "", 0, 0.0):
			return f"the {item_name} item on this invoice"
		return f"the {item_name} on this invoice"
	if item_rows:
		return "the items on this invoice"
	return "this invoice"


def _delivery_note_phrase(delivery_notes: List[str]) -> str:
	if not delivery_notes:
		return "submitted delivery note records"
	if len(delivery_notes) == 1:
		return f"submitted Delivery Note {delivery_notes[0]}"
	if len(delivery_notes) <= 3:
		return "submitted Delivery Notes " + ", ".join(delivery_notes[:-1]) + f", and {delivery_notes[-1]}"
	return "submitted Delivery Notes " + ", ".join(delivery_notes[:3]) + ", ..."


def _sentence_case(text: str) -> str:
	value = str(text or "").strip()
	if not value:
		return ""
	return value[:1].upper() + value[1:]


def _delivery_date_phrase(delivery_dates: List[str]) -> str:
	if not delivery_dates:
		return ""
	if len(delivery_dates) == 1:
		return delivery_dates[0]
	if len(delivery_dates) == 2:
		return f"{delivery_dates[0]} and {delivery_dates[1]}"
	return ", ".join(delivery_dates[:-1]) + f", and {delivery_dates[-1]}"


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _money(value: Any) -> str:
	return f"{_numeric(value):,.2f}".rstrip("0").rstrip(".")


def _summary_block(title: str, rows: List[List[str]]) -> Dict[str, Any]:
	return {
		"block_type": "summary_table",
		"title": str(title or "").strip(),
		"columns": ["Field", "Value"],
		"rows": [
			[str(label or "").strip(), str(value or "").strip()]
			for label, value in rows
			if str(label or "").strip() and str(value or "").strip()
		],
	}


def _data_block(title: str, columns: List[str], rows: List[List[str]]) -> Dict[str, Any]:
	return {
		"block_type": "data_table",
		"title": str(title or "").strip(),
		"columns": [str(value or "").strip() for value in (columns or []) if str(value or "").strip()],
		"rows": [
			[str(cell or "").strip() for cell in row]
			for row in (rows or [])
			if isinstance(row, list)
		],
	}


def _bullet_block(title: str, items: List[str]) -> Dict[str, Any]:
	return {
		"block_type": "bullet_list",
		"title": str(title or "").strip(),
		"items": [str(value or "").strip() for value in (items or []) if str(value or "").strip()],
	}


def _join_values(values: List[str]) -> str:
	clean = [str(value or "").strip() for value in (values or []) if str(value or "").strip()]
	if not clean:
		return ""
	if len(clean) == 1:
		return clean[0]
	if len(clean) == 2:
		return f"{clean[0]} and {clean[1]}"
	return ", ".join(clean[:-1]) + f", and {clean[-1]}"


def build_grounded_artifact_direct_evidence_rendered_payload(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> Dict[str, Any]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	if str(artifact.get("family_id") or "").strip() != "entity_detail":
		return {}
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	entity_type = str(dimensions.get("entity_type") or "").strip().lower()
	if entity_type == "sales_order":
		request_concepts = {
			str(value or "").strip()
			for value in ontology_detect_concepts(raw_message)
			if str(value or "").strip()
		}
		requested_dimensions = set(
			detect_canonical_keys(
				raw_message,
				capability_id="sales_order_read",
				dimension_or_metric="dimension",
			)
		)
		requested_metrics = set(
			detect_canonical_keys(
				raw_message,
				capability_id="sales_order_read",
				dimension_or_metric="metric",
			)
		)
		if "posting_date" in requested_dimensions and "planned_delivery_date" not in requested_dimensions and "fulfillment" in request_concepts:
			return {}
		if not requested_dimensions.intersection({"document_status", "planned_delivery_date"}) and not requested_metrics.intersection(
			{"delivery_progress_percent", "billing_progress_percent"}
		) and "fulfillment" not in request_concepts:
			return {}
		document_row = _artifact_document_row(artifact)
		item_rows = _artifact_item_rows(artifact)
		entity_label = str(dimensions.get("entity_label") or dimensions.get("entity_key") or "Sales Order").strip()
		customer = str(document_row.get("customer") or "").strip()
		status = str(document_row.get("status") or "").strip()
		delivery_status = str(document_row.get("delivery_status") or "").strip()
		billing_status = str(document_row.get("billing_status") or "").strip()
		planned_delivery_date = str(document_row.get("delivery_date") or "").strip()
		per_delivered = _numeric(document_row.get("per_delivered"))
		per_billed = _numeric(document_row.get("per_billed"))
		total_qty = _numeric(document_row.get("quantity"))
		delivered_qty = sum(_numeric(row.get("delivered_qty")) for row in item_rows)
		billed_amount = sum(_numeric(row.get("billed_amount")) for row in item_rows)
		evidence_rows = [
			["Sales Order", entity_label],
			["Customer", customer],
			["Current Status", status],
			["Delivery Status", delivery_status],
			["Billing Status", billing_status],
			["Planned Delivery Date", planned_delivery_date],
			["Delivered (%)", _money(per_delivered)],
			["Billed (%)", _money(per_billed)],
		]
		evidence_items: List[str] = []
		if "document_status" in requested_dimensions:
			evidence_items.append(
				f"The current sales order status is {status}, with delivery status {delivery_status or 'Unknown'} and billing status {billing_status or 'Unknown'}."
			)
		if "planned_delivery_date" in requested_dimensions and planned_delivery_date:
			evidence_items.append(f"The planned delivery date recorded on the sales order is {planned_delivery_date}.")
		if "delivery_progress_percent" in requested_metrics or "fulfillment" in request_concepts:
			delivery_item = f"Delivery progress is {_money(per_delivered)}%"
			if delivery_status:
				delivery_item += f" ({delivery_status})"
			if total_qty > 0:
				delivery_item += f", with { _money(delivered_qty) } of { _money(total_qty) } units delivered on the current order lines"
			evidence_items.append(delivery_item + ".")
		if "billing_progress_percent" in requested_metrics:
			billing_item = f"Billing progress is {_money(per_billed)}%"
			if billing_status:
				billing_item += f" ({billing_status})"
			if billed_amount > 0:
				billing_item += f", with {_money(billed_amount)} MMK billed on the current order lines"
			evidence_items.append(billing_item + ".")
		item_table_rows = [
			[
				str(row.get("item_code") or "").strip(),
				str(row.get("item_name") or "").strip(),
				_money(row.get("qty")),
				_money(row.get("delivered_qty")),
				_money(row.get("billed_amount")),
			]
			for row in item_rows
		]
		return {
			"type": "qwen_rendered_family_response_contract",
			"contract_version": "1.0",
			"request_id": str(artifact.get("request_id") or "").strip(),
			"family_id": str(artifact.get("family_id") or "").strip(),
			"renderer_id": "grounded_artifact_direct_evidence",
			"title": f"Order Status Evidence for {entity_label}",
			"answer_text": "",
			"source_reports": [
				str(value or "").strip()
				for value in (artifact.get("source_reports") or [])
				if str(value or "").strip()
			],
			"blocks": [
				_summary_block("Order Status Evidence", evidence_rows),
				_data_block(
					"Order Items",
					["Item Code", "Item Name", "Qty", "Delivered Qty", "Billed Amount (MMK)"],
					item_table_rows,
				),
				_bullet_block("Evidence Highlights", evidence_items),
			],
			"warnings": [
				str(value or "").strip()
				for value in (artifact.get("warnings") or [])
				if str(value or "").strip()
			],
		}
	if entity_type != "sales_invoice":
		return {}
	delivery_proof = _artifact_delivery_proof(artifact)
	proof_state = str(delivery_proof.get("proof_state") or "").strip()
	if proof_state not in {
		"direct_delivery_proven_via_invoice_stock",
		"direct_delivery_proven_via_linked_delivery_note",
		"direct_return_proven_via_invoice_stock",
		"direct_return_proven_via_linked_delivery_note",
	}:
		return {}
	document_row = _artifact_document_row(artifact)
	item_rows = _artifact_item_rows(artifact)
	entity_label = str(dimensions.get("entity_label") or dimensions.get("entity_key") or "Sales Invoice").strip()
	customer = str(document_row.get("customer") or "").strip()
	subject_phrase = _sentence_case(_delivery_subject_phrase(item_rows))
	delivery_dates = [
		str(value or "").strip()
		for value in (delivery_proof.get("submitted_delivery_dates") or [])
		if str(value or "").strip()
	]
	delivery_note_names = [
		str(value or "").strip()
		for value in (delivery_proof.get("submitted_delivery_notes") or [])
		if str(value or "").strip()
	]
	sales_orders = [
		str(value or "").strip()
		for value in (delivery_proof.get("sales_orders") or [])
		if str(value or "").strip()
	]
	delivery_note_rows = [
		dict(row or {})
		for row in (delivery_proof.get("delivery_notes") or [])
		if isinstance(row, dict) and int(row.get("docstatus") or 0) == 1
	]
	proof_method = str(delivery_proof.get("proof_method") or "").strip()
	is_return = proof_state.startswith("direct_return_")
	status_label = "Return Recorded" if is_return else "Delivered"
	basis_label = "Submitted stock-updating invoice" if proof_method == "invoice_stock" else "Submitted delivery note linkage"
	evidence_rows = [
		["Invoice", entity_label],
		["Customer", customer],
		["Fulfillment Status", status_label],
		["Evidence Basis", basis_label],
		["Invoice Subject", subject_phrase],
	]
	delivery_date_text = _delivery_date_phrase(delivery_dates)
	if delivery_date_text:
		evidence_rows.append(["Recorded Delivery Date", delivery_date_text])
	if delivery_note_names:
		evidence_rows.append(["Linked Delivery Notes", _join_values(delivery_note_names)])
	if sales_orders:
		evidence_rows.append(["Linked Sales Orders", _join_values(sales_orders)])
	evidence_items: List[str] = []
	if proof_method == "invoice_stock":
		evidence_items.append(
			f"{entity_label} was submitted with stock update enabled, so the stock movement was recorded directly on the invoice."
		)
	elif delivery_note_names:
		evidence_items.append(
			f"All invoice items are linked to submitted delivery note records: {_join_values(delivery_note_names)}."
		)
	if delivery_date_text:
		evidence_items.append(f"Recorded delivery date: {delivery_date_text}.")
	if sales_orders:
		evidence_items.append(f"Related sales order reference: {_join_values(sales_orders)}.")
	if is_return:
		evidence_items.append(
			"This invoice represents a return/reversal context rather than a normal outbound delivery confirmation."
		)
	linked_note_table_rows = [
		[
			str(row.get("delivery_note") or "").strip(),
			str(row.get("posting_date") or "").strip(),
			str(row.get("status") or "").strip(),
			str(row.get("return_against") or "").strip(),
		]
		for row in delivery_note_rows
	]
	source_reports = [
		str(value or "").strip()
		for value in (artifact.get("source_reports") or [])
		if str(value or "").strip()
	]
	if delivery_note_names and "Delivery Note" not in source_reports:
		source_reports.append("Delivery Note")
	blocks: List[Dict[str, Any]] = [
		_summary_block("Delivery Evidence", evidence_rows),
	]
	if linked_note_table_rows:
		blocks.append(
			_data_block(
				"Linked Delivery Notes",
				["Delivery Note", "Posting Date", "Status", "Return Against"],
				linked_note_table_rows,
			)
		)
	if evidence_items:
		blocks.append(_bullet_block("Evidence Highlights", evidence_items))
	return {
		"type": "qwen_rendered_family_response_contract",
		"contract_version": "1.0",
		"request_id": str(artifact.get("request_id") or "").strip(),
		"family_id": str(artifact.get("family_id") or "").strip(),
		"renderer_id": "grounded_artifact_direct_evidence",
		"title": f"Delivery Evidence for {entity_label}",
		"answer_text": "",
		"source_reports": source_reports,
		"blocks": blocks,
		"warnings": [
			str(value or "").strip()
			for value in (artifact.get("warnings") or [])
			if str(value or "").strip()
		],
	}


def grounded_artifact_direct_evidence_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	if str(artifact.get("family_id") or "").strip() != "entity_detail":
		return ""
	request_concepts = {
		str(value or "").strip()
		for value in ontology_detect_concepts(raw_message)
		if str(value or "").strip()
	}
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	entity_type = str(dimensions.get("entity_type") or "").strip().lower()
	if entity_type == "sales_order":
		requested_dimensions = set(
			detect_canonical_keys(
				raw_message,
				capability_id="sales_order_read",
				dimension_or_metric="dimension",
			)
		)
		requested_metrics = set(
			detect_canonical_keys(
				raw_message,
				capability_id="sales_order_read",
				dimension_or_metric="metric",
			)
		)
		if "posting_date" in requested_dimensions and "planned_delivery_date" not in requested_dimensions and "fulfillment" in request_concepts:
			return ""
		if not requested_dimensions.intersection({"document_status", "planned_delivery_date"}) and not requested_metrics.intersection(
			{"delivery_progress_percent", "billing_progress_percent"}
		) and "fulfillment" not in request_concepts:
			return ""
		document_row = _artifact_document_row(artifact)
		item_rows = _artifact_item_rows(artifact)
		entity_label = str(dimensions.get("entity_label") or dimensions.get("entity_key") or "this sales order").strip()
		customer = str(document_row.get("customer") or "").strip()
		customer_phrase = f" for {customer}" if customer else ""
		status = str(document_row.get("status") or "").strip()
		delivery_status = str(document_row.get("delivery_status") or "").strip()
		billing_status = str(document_row.get("billing_status") or "").strip()
		planned_delivery_date = str(document_row.get("delivery_date") or "").strip()
		per_delivered = _numeric(document_row.get("per_delivered"))
		per_billed = _numeric(document_row.get("per_billed"))
		total_qty = _numeric(document_row.get("quantity"))
		delivered_qty = sum(_numeric(row.get("delivered_qty")) for row in item_rows)
		billed_amount = sum(_numeric(row.get("billed_amount")) for row in item_rows)
		if "planned_delivery_date" in requested_dimensions and planned_delivery_date:
			return f"The planned delivery date for {entity_label}{customer_phrase} is {planned_delivery_date}."
		if "billing_progress_percent" in requested_metrics:
			if per_billed >= 100:
				return (
					f"Yes. {entity_label} is fully billed{customer_phrase}.\n\n"
					f"Billing progress is {_money(per_billed)}% ({billing_status or 'Fully Billed'})."
				)
			if per_billed <= 0:
				return (
					f"No. {entity_label} has not been billed yet{customer_phrase}.\n\n"
					f"Billing progress is {_money(per_billed)}% ({billing_status or 'Not Billed'})."
				)
			detail = f"Only {_money(per_billed)}% has been billed so far"
			if billed_amount > 0:
				detail += f", which is {_money(billed_amount)} MMK on the current order lines"
			return f"Partly. {entity_label} is not fully billed yet{customer_phrase}.\n\n{detail} ({billing_status or 'Partly Billed'})."
		if "document_status" in requested_dimensions:
			return (
				f"The current status of {entity_label}{customer_phrase} is {status}.\n\n"
				f"Delivery status is {delivery_status or 'Unknown'}, and billing status is {billing_status or 'Unknown'}."
			)
		if "delivery_progress_percent" in requested_metrics or "fulfillment" in request_concepts:
			if per_delivered >= 100:
				return (
					f"Yes. {entity_label} is fully delivered{customer_phrase}.\n\n"
					f"Delivery progress is {_money(per_delivered)}% ({delivery_status or 'Fully Delivered'})."
				)
			if per_delivered <= 0:
				return (
					f"No. {entity_label} has not been delivered yet{customer_phrase}.\n\n"
					f"Delivery progress is {_money(per_delivered)}% ({delivery_status or 'Not Delivered'})."
				)
			detail = f"It is {_money(per_delivered)}% delivered so far"
			if total_qty > 0:
				detail += f", with {_money(delivered_qty)} of {_money(total_qty)} units delivered on the current order lines"
			return f"Partly. {entity_label} is not fully delivered yet{customer_phrase}.\n\n{detail} ({delivery_status or 'Partly Delivered'})."
		return ""
	if "fulfillment" not in request_concepts:
		return ""
	if entity_type != "sales_invoice":
		return ""
	delivery_proof = _artifact_delivery_proof(artifact)
	proof_state = str(delivery_proof.get("proof_state") or "").strip()
	entity_label = str(dimensions.get("entity_label") or dimensions.get("entity_key") or "this invoice").strip()
	document_row = _artifact_document_row(artifact)
	item_rows = _artifact_item_rows(artifact)
	subject_phrase = _delivery_subject_phrase(item_rows)
	customer = str(document_row.get("customer") or "").strip()
	customer_phrase = f" to {customer}" if customer else ""
	requested_dimensions = set(detect_canonical_keys(raw_message, dimension_or_metric="dimension"))
	wants_posting_date = "posting_date" in requested_dimensions
	delivery_notes = [
		str(value or "").strip()
		for value in (delivery_proof.get("submitted_delivery_notes") or [])
		if str(value or "").strip()
	]
	delivery_dates = [
		str(value or "").strip()
		for value in (delivery_proof.get("submitted_delivery_dates") or [])
		if str(value or "").strip()
	]
	document_posting_date = str(document_row.get("posting_date") or "").strip()
	if proof_state == "direct_delivery_proven_via_invoice_stock":
		if wants_posting_date and document_posting_date:
			return (
				f"It was delivered on {document_posting_date}{customer_phrase}.\n\n"
				f"{entity_label} is a submitted stock-updating invoice, so the stock movement was recorded directly on the invoice."
			)
		return (
			f"Yes. {_sentence_case(subject_phrase)} has already been delivered{customer_phrase}.\n\n"
			f"{entity_label} is a submitted stock-updating invoice, so the stock movement was recorded directly on the invoice."
		)
	if proof_state == "direct_delivery_proven_via_linked_delivery_note":
		delivery_note_text = _delivery_note_phrase(delivery_notes)
		delivery_date_text = _delivery_date_phrase(delivery_dates)
		if wants_posting_date and delivery_date_text:
			return (
				f"It was delivered on {delivery_date_text}{customer_phrase} through {delivery_note_text}.\n\n"
				f"All invoice items on {entity_label} are linked to that submitted delivery record."
			)
		return (
			f"Yes. {_sentence_case(subject_phrase)} has already been delivered{customer_phrase}.\n\n"
			f"All invoice items on {entity_label} are linked to {delivery_note_text}."
		)
	if proof_state == "direct_return_proven_via_invoice_stock":
		if wants_posting_date and document_posting_date:
			return (
				f"The return movement was posted on {document_posting_date}.\n\n"
				"The submitted invoice recorded the stock reversal directly."
			)
		return (
			f"{entity_label} is a return invoice, so this is reversal evidence rather than a normal outbound delivery confirmation.\n\n"
			"The submitted invoice posted the return stock movement directly."
		)
	if proof_state == "direct_return_proven_via_linked_delivery_note":
		delivery_note_text = _delivery_note_phrase(delivery_notes)
		delivery_date_text = _delivery_date_phrase(delivery_dates)
		if wants_posting_date and delivery_date_text:
			return (
				f"The linked return movement was posted on {delivery_date_text}.\n\n"
				f"The governed reversal evidence comes from {delivery_note_text}."
			)
		return (
			f"{entity_label} is a return invoice, so this is reversal evidence rather than a normal outbound delivery confirmation.\n\n"
			f"The return is linked to {delivery_note_text}."
		)
	return ""


def grounded_artifact_evidence_boundary_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	if str(artifact.get("family_id") or "").strip() not in {"entity_detail", "transaction_listing"}:
		return ""
	entity_type = ""
	if isinstance(artifact.get("dimensions"), dict):
		entity_type = str((artifact.get("dimensions") or {}).get("entity_type") or "").strip().lower()
	if entity_type == "sales_order":
		request_concepts = {
			str(value or "").strip()
			for value in ontology_detect_concepts(raw_message)
			if str(value or "").strip()
		}
		requested_dimensions = set(
			detect_canonical_keys(
				raw_message,
				capability_id="sales_order_read",
				dimension_or_metric="dimension",
			)
		)
		if "posting_date" in requested_dimensions and "planned_delivery_date" not in requested_dimensions and "fulfillment" in request_concepts:
			return (
				"The current sales order shows planned delivery date and delivery progress, but it does not prove the actual shipment event date.\n\n"
				"To answer when it was actually delivered, I need governed downstream fulfillment evidence such as linked delivery-note records."
			)
	request_concepts = {
		str(value or "").strip()
		for value in ontology_detect_concepts(raw_message)
		if str(value or "").strip()
	}
	if not request_concepts:
		return ""
	evidence_concepts = artifact_evidence_concepts(artifact, grounded_turn)
	if entity_type in {"sales_invoice", "purchase_invoice"}:
		evidence_concepts = {concept for concept in evidence_concepts if concept != "fulfillment"}
	missing_concepts = request_concepts.difference(evidence_concepts)
	high_risk_missing = [concept for concept in missing_concepts if concept in {"fulfillment"}]
	if not high_risk_missing:
		return ""
	concept_aliases = ontology_concept_aliases(high_risk_missing[0])
	concept_label = str(concept_aliases[0] or "").strip() if concept_aliases else high_risk_missing[0].replace("_", " ")
	return (
		"The current governed artifact does not include direct fields proving that "
		f"{concept_label} status, so I can't confirm it confidently from this artifact alone.\n\n"
		"I can confirm the billing and payment fields shown here, but this question needs governed operational evidence such as "
		"delivery or stock-movement records."
	)


def artifact_enrichment_boundary_answer(
	*,
	followup_resolution,
	compatibility_contract,
) -> str:
	source_capability_id = str(getattr(compatibility_contract, "source_capability_id", "") or "").strip()
	requested_columns = [
		str(item or "").strip()
		for item in (getattr(followup_resolution, "requested_columns", []) or [])
		if str(item or "").strip()
	]
	target_metric = str(getattr(followup_resolution, "target_metric", "") or "").strip()

	def _label_for(value: str) -> str:
		canonical = get_canonical_key(value, capability_id=source_capability_id or None, dimension_or_metric="metric")
		if canonical:
			return str(get_metric_label(canonical) or value or "").strip()
		return str(value or "").replace("_", " ").strip()

	def _join_labels(values: List[str]) -> str:
		clean = [str(value or "").strip() for value in values if str(value or "").strip()]
		if not clean:
			return ""
		if len(clean) == 1:
			return clean[0]
		return ", ".join(clean[:-1]) + f", and {clean[-1]}"

	requested_targets = list(requested_columns or ([target_metric] if target_metric else []))
	raw_requested = [value for value in requested_targets if value]
	requested_labels = []
	for value in requested_targets:
		label = _label_for(value)
		if label and label not in requested_labels:
			requested_labels.append(label)
	label_text = _join_labels(requested_labels) or "the requested columns or metrics"
	base_metric_label = _label_for(target_metric) if target_metric else ""
	source_report = str(getattr(compatibility_contract, "source_report", "") or "").strip()
	report_basis = source_report or "the current governed report"
	missing_reason = str(getattr(compatibility_contract, "reason", "") or "").strip()
	if raw_requested:
		return (
			f"The current governed source cannot safely add {label_text} from {report_basis}.\n\n"
			f"This artifact does not expose those requested fields directly, so this follow-up needs a governed requery instead of local reshaping."
			+ (f"\n\nWhy: {missing_reason}" if missing_reason else "")
		)
	if base_metric_label:
		return (
			f"The current governed source cannot safely switch this artifact to {base_metric_label} from {report_basis}.\n\n"
			"This follow-up needs a governed requery because the requested metric is not directly populated in the current grounded artifact."
			+ (f"\n\nWhy: {missing_reason}" if missing_reason else "")
		)
	return (
		f"The current governed source cannot safely produce that enriched output from {report_basis}.\n\n"
		"This follow-up needs a governed requery instead of local reshaping."
		+ (f"\n\nWhy: {missing_reason}" if missing_reason else "")
	)


def knowledge_boundary_event_level(boundary_payload: Dict[str, Any]) -> str:
	coverage_state = str(boundary_payload.get("knowledge_coverage_state") or "").strip().lower()
	boundary_status = str(boundary_payload.get("boundary_status") or "").strip().lower()
	if coverage_state in {"valid_erp_domain_uncovered", "unsupported_non_erp"}:
		return "warning"
	if boundary_status in {"blocked", "reclassified"}:
		return "warning"
	return "info"


def append_knowledge_boundary_observability(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	boundary_payload: Dict[str, Any],
	latency_ms: int,
	append_tool_payload,
) -> None:
	coverage_state = str(boundary_payload.get("knowledge_coverage_state") or "").strip()
	append_tool_payload(
		session_doc,
		record_phase6_observability_event(
			request_id=request_id,
			session_id=session_id,
			event_family="knowledge_boundary",
			event_name=coverage_state or "answered",
			event_level=knowledge_boundary_event_level(boundary_payload),
			details={
				"final_lane": str(boundary_payload.get("final_lane") or "").strip(),
				"safe_next_action": str(boundary_payload.get("safe_next_action") or "").strip(),
				"user_response_mode": str(boundary_payload.get("user_response_mode") or "").strip(),
				"latency_ms": int(max(0, latency_ms)),
			},
		),
	)
	append_tool_payload(
		session_doc,
		record_phase6_performance_metric(
			request_id=request_id,
			session_id=session_id,
			metric_name="knowledge_boundary_latency",
			metric_value=float(max(0, latency_ms)),
			metric_unit="ms",
			details={
				"knowledge_coverage_state": coverage_state,
				"final_lane": str(boundary_payload.get("final_lane") or "").strip(),
			},
		),
	)


def append_artifact_boundary_observability(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	boundary_name: str,
	latency_ms: int,
	recovery_payload: Dict[str, Any] | None = None,
	grounded_turn_available: bool = False,
	append_tool_payload,
) -> None:
	recovery = dict(recovery_payload or {})
	append_tool_payload(
		session_doc,
		record_phase6_observability_event(
			request_id=request_id,
			session_id=session_id,
			event_family="artifact_boundary",
			event_name=str(boundary_name or "").strip() or "artifact_boundary",
			event_level="warning",
			details={
				"recommended_recovery_action": str(recovery.get("recommended_recovery_action") or "").strip(),
				"recovery_state": str(recovery.get("recovery_state") or "").strip(),
				"source_report": str(recovery.get("source_report") or "").strip(),
				"grounded_context_available": bool(grounded_turn_available),
				"latency_ms": int(max(0, latency_ms)),
			},
		),
	)
	append_tool_payload(
		session_doc,
		record_phase6_performance_metric(
			request_id=request_id,
			session_id=session_id,
			metric_name=f"{str(boundary_name or '').strip() or 'artifact_boundary'}_latency",
			metric_value=float(max(0, latency_ms)),
			metric_unit="ms",
			details={
				"recommended_recovery_action": str(recovery.get("recommended_recovery_action") or "").strip(),
				"recovery_state": str(recovery.get("recovery_state") or "").strip(),
			},
		),
	)


def artifact_evidence_concepts(artifact_payload: Dict[str, Any], grounded_turn: Dict[str, Any]) -> set[str]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	parts: List[str] = []
	parts.extend(str(item or "").strip() for item in (artifact.get("source_reports") or []) if str(item or "").strip())
	parts.extend(
		str(value or "").strip()
		for value in (
			artifact.get("family_id"),
			(artifact.get("dimensions") or {}).get("entity_type") if isinstance(artifact.get("dimensions"), dict) else "",
			(artifact.get("dimensions") or {}).get("source_grain") if isinstance(artifact.get("dimensions"), dict) else "",
			turn.get("source_name"),
		)
		if str(value or "").strip()
	)
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	parts.extend(str(key or "").strip() for key in dimensions.keys() if str(key or "").strip())
	parts.extend(str(key or "").strip() for key in metrics.keys() if str(key or "").strip())
	parts.extend(str(key or "").strip() for key in sections.keys() if str(key or "").strip())
	for value in sections.values():
		if isinstance(value, list):
			for row in value[:3]:
				if isinstance(row, dict):
					parts.extend(str(key or "").strip() for key in row.keys() if str(key or "").strip())
	joined = " ".join(part for part in parts if part)
	return {
		str(value or "").strip()
		for value in ontology_detect_concepts(joined)
		if str(value or "").strip()
	}
