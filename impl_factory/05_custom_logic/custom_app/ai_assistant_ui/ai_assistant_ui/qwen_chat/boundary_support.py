from __future__ import annotations

import re
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import build_entity_detail_evidence_request_contract
from ai_assistant_ui.qwen_chat.composite_evidence_support import (
	composite_ranked_row_evidence_boundary_answer,
	composite_ranked_row_direct_evidence_answer,
	composite_ranked_row_direct_evidence_rendered_payload,
)
from ai_assistant_ui.qwen_chat.customer_boundary_answer_support import customer_boundary_direct_evidence_answer
from ai_assistant_ui.qwen_chat.evidence_expansion_support import (
	build_evidence_expansion_plan,
	evidence_expansion_user_guidance,
)
from ai_assistant_ui.qwen_chat.item_stock_boundary_support import (
	item_stock_direct_evidence_answer,
	item_stock_direct_evidence_rendered_payload,
	item_stock_evidence_boundary_answer,
)
from ai_assistant_ui.qwen_chat.metadata import ontology_concept_aliases, ontology_detect_concepts
from ai_assistant_ui.qwen_chat.observability import (
	record_phase6_observability_event,
	record_phase6_performance_metric,
)
from ai_assistant_ui.qwen_chat.semantic_resolution_registry import semantic_alias_phrase_matches
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys, get_canonical_key, get_metric_label
from ai_assistant_ui.qwen_chat.supplier_boundary_answer_support import supplier_boundary_direct_evidence_answer


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


def _normalized_phrase(value: Any) -> str:
	return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _artifact_title(artifact: Dict[str, Any]) -> str:
	title = str(artifact.get("title") or artifact.get("report_title") or artifact.get("report_name") or "").strip()
	if title:
		return title
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	statement_type = str(dimensions.get("statement_type") or "").strip()
	if statement_type:
		return statement_type.replace("_", " ").title()
	family_id = str(artifact.get("family_id") or "").strip()
	return family_id.replace("_", " ").title() if family_id else "ERP result"


def _artifact_sections(artifact: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	out: Dict[str, List[Dict[str, Any]]] = {}
	for section_key, rows in sections.items():
		if not isinstance(rows, list):
			continue
		clean_rows = [dict(row) for row in rows if isinstance(row, dict)]
		if clean_rows:
			out[str(section_key or "").strip()] = clean_rows
	return {key: value for key, value in out.items() if key and value}


def _section_label(section_key: str) -> str:
	return str(section_key or "").strip().replace("_", " ").title()


def _singular_candidates(value: str) -> List[str]:
	text = str(value or "").strip()
	candidates = [text]
	if text.endswith("ies") and len(text) > 3:
		candidates.append(text[:-3] + "y")
	elif text.endswith("s") and len(text) > 1:
		candidates.append(text[:-1])
	return list(dict.fromkeys(candidate for candidate in candidates if candidate))


def _row_label(row: Dict[str, Any]) -> str:
	for key in (
		"label",
		"account",
		"metric",
		"line",
		"name",
		"bucket",
		"item_name",
		"item_code",
		"customer",
		"supplier",
		"warehouse",
		"sales_invoice",
		"purchase_invoice",
		"document_name",
		"document",
	):
		value = str(row.get(key) or "").strip()
		if value:
			return value
	return ""


def _row_label_acronyms(label: str) -> List[str]:
	words = [
		token
		for token in re.findall(r"[A-Za-z0-9]+", str(label or ""))
		if token
	]
	if len(words) < 2:
		return []
	acronyms: List[str] = []
	all_words = "".join(word[:1].upper() for word in words if word[:1]).strip()
	if all_words:
		acronyms.append(all_words)
	significant_words = [
		word
		for word in words
		if word.lower() not in {"and", "or", "of", "the", "a", "an"}
	]
	if len(significant_words) >= 2:
		significant = "".join(word[:1].upper() for word in significant_words if word[:1]).strip()
		if significant:
			acronyms.append(significant)
	return list(dict.fromkeys(acronym for acronym in acronyms if len(acronym) >= 3))


def _row_target_phrases(row: Dict[str, Any]) -> List[str]:
	label = _row_label(row)
	phrases = [label]
	phrases.extend(_row_label_acronyms(label))
	return list(dict.fromkeys(phrase for phrase in phrases if _normalized_phrase(phrase)))


def _section_target_phrases(section_key: str, rows: List[Dict[str, Any]]) -> List[str]:
	phrases: List[str] = []
	for candidate in _singular_candidates(str(section_key or "").strip().replace("_", " ")):
		phrases.append(candidate)
	for row in rows:
		phrases.extend(_row_target_phrases(row))
	return list(dict.fromkeys(phrase for phrase in phrases if _normalized_phrase(phrase)))


def _artifact_surface_concept(artifact: Dict[str, Any]) -> str:
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	statement_type = str(dimensions.get("statement_type") or "").strip()
	if statement_type:
		return statement_type
	return str(artifact.get("concept_id") or artifact.get("artifact_concept") or "").strip()


def _message_requests_different_artifact_surface(raw_message: str, artifact: Dict[str, Any]) -> bool:
	current_surface = _artifact_surface_concept(artifact)
	if not current_surface:
		return False
	try:
		concepts = ontology_detect_concepts(raw_message)
	except Exception:
		concepts = []
	for concept in concepts:
		clean = str(concept or "").strip()
		if clean and clean != current_surface:
			return True
	return False


def _artifact_section_from_message(raw_message: str, artifact: Dict[str, Any]) -> str:
	if _message_requests_different_artifact_surface(raw_message, artifact):
		return ""
	sections = _artifact_sections(artifact)
	best_key = ""
	best_score = -1
	for section_key, rows in sections.items():
		for phrase in _section_target_phrases(section_key, rows):
			if not semantic_alias_phrase_matches(raw_message, phrase):
				continue
			score = len(_normalized_phrase(phrase))
			if score > best_score:
				best_key = section_key
				best_score = score
	return best_key


def _artifact_line_from_message(raw_message: str, artifact: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
	if _message_requests_different_artifact_surface(raw_message, artifact):
		return "", {}
	sections = _artifact_sections(artifact)
	best_key = ""
	best_row: Dict[str, Any] = {}
	best_score = -1
	for section_key, rows in sections.items():
		for row in rows:
			for phrase in _row_target_phrases(row):
				if not semantic_alias_phrase_matches(raw_message, phrase):
					continue
				score = len(_normalized_phrase(phrase))
				if score > best_score:
					best_key = section_key
					best_row = dict(row)
					best_score = score
	return best_key, best_row


def _metric_total_for_section(section_key: str, artifact: Dict[str, Any]) -> Any:
	metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
	section_terms = {
		_normalized_phrase(candidate).replace(" ", "_")
		for candidate in _singular_candidates(str(section_key or "").strip().replace("_", " "))
		if _normalized_phrase(candidate)
	}
	if not section_terms:
		return None
	for metric_key, metric_value in metrics.items():
		normalized_key = _normalized_phrase(metric_key).replace(" ", "_")
		if not normalized_key:
			continue
		if any(term and term in normalized_key for term in section_terms):
			return metric_value
	return None


def _metric_value_by_key(artifact: Dict[str, Any], *keys: str) -> Any:
	metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
	wanted = {
		_normalized_phrase(key).replace(" ", "_")
		for key in keys
		if _normalized_phrase(key)
	}
	for metric_key, metric_value in metrics.items():
		if _normalized_phrase(metric_key).replace(" ", "_") in wanted:
			return metric_value
	return None


def _section_rows(section_key: str, artifact: Dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	rows = [dict(row) for row in (sections.get(section_key) or []) if isinstance(row, dict)]
	clean_rows = [
		row
		for row in rows
		if _row_label(row)
		and abs(_numeric(row.get("amount"))) > 0.0001
	]
	clean_rows.sort(key=lambda row: abs(_numeric(row.get("amount"))), reverse=True)
	return clean_rows[: max(1, int(limit or 8))]


def _section_row_columns(rows: List[Dict[str, Any]]) -> List[str]:
	preferred = [
		"label",
		"account",
		"metric",
		"line",
		"bucket",
		"item_name",
		"item_code",
		"customer",
		"supplier",
		"warehouse",
		"amount",
		"value",
		"qty",
		"quantity",
		"outstanding",
		"overdue",
	]
	seen: List[str] = []
	for key in preferred:
		if any(str(row.get(key) or "").strip() for row in rows):
			seen.append(key)
	for row in rows:
		for key in row.keys():
			if key not in seen and str(row.get(key) or "").strip():
				seen.append(key)
			if len(seen) >= 5:
				return seen
	return seen[:5]


def _human_column_label(key: str) -> str:
	return str(key or "").strip().replace("_", " ").title()


def _format_section_cell(key: str, value: Any, currency: str) -> str:
	clean_key = str(key or "").strip().lower()
	if clean_key in {"amount", "value", "outstanding", "overdue", "total_due", "grand_total"}:
		return f"{_money(value)} {currency}"
	return str(value or "").strip()


def _business_account_label(value: Any) -> str:
	value_text = str(value or "").strip()
	if not value_text:
		return ""
	if " - " in value_text:
		return value_text.split(" - ", 1)[0].strip()
	return value_text


def _line_item_business_category(row: Dict[str, Any]) -> str:
	parent = _business_account_label(row.get("parent_account"))
	label = _business_account_label(row.get("label"))
	if parent and parent != label:
		return parent
	return ""


def _line_item_detail_answer(
	*,
	section_key: str,
	row: Dict[str, Any],
	artifact: Dict[str, Any],
	currency: str,
) -> str:
	line_label = _row_label(row)
	if not line_label:
		return ""
	section_label = _section_label(section_key)
	artifact_title = _artifact_title(artifact)
	total_value = _metric_total_for_section(section_key, artifact)
	amount = _numeric(row.get("amount") if row.get("amount") not in (None, "") else row.get("value"))
	total_income = _metric_value_by_key(artifact, "total_income")
	lines: List[str] = [
		f"{line_label} is shown under {section_label} in the current {artifact_title}.",
		"",
		"Business facts:",
		f"- Amount: {_money(amount)} {currency}",
	]
	if total_value not in (None, "") and abs(_numeric(total_value)) > 0.0001:
		lines.append(f"- Share of {section_label.lower()}: {abs(amount) / abs(_numeric(total_value)) * 100:.1f}%")
	if total_income not in (None, "") and abs(_numeric(total_income)) > 0.0001:
		lines.append(f"- Share of income: {abs(amount) / abs(_numeric(total_income)) * 100:.1f}%")
	category = _line_item_business_category(row)
	if category:
		lines.append(f"- Business category: {category}")
	interpretation: List[str] = []
	absolute_amount = abs(amount)
	if total_value not in (None, "") and abs(_numeric(total_value)) > 0.0001:
		share = absolute_amount / abs(_numeric(total_value)) * 100
		interpretation.append(
			f"This line represents {share:.1f}% of {section_label.lower()}, so it is a material driver rather than a minor variance."
		)
	if total_income not in (None, "") and abs(_numeric(total_income)) > 0.0001:
		income_share = absolute_amount / abs(_numeric(total_income)) * 100
		interpretation.append(
			f"Relative to total income, this line consumes {income_share:.1f}% of revenue, so it has direct margin impact."
		)
		remainder = _numeric(total_income) - absolute_amount
		interpretation.append(
			f"After this line alone, the remaining margin room before other expenses is {_money(remainder)} {currency}."
		)
	if interpretation:
		lines.append("")
		lines.append("Consultant view:")
		lines.extend(f"- {item}" for item in interpretation)
	expansion_plan = build_evidence_expansion_plan(
		grounding_context={
			"evidence_policy": "evidence_expansion_preferred",
			"answer_obligation": "expand_grounded_detail",
			"grounded_source": {
				"family_id": str(artifact.get("family_id") or "").strip(),
				"source_name": artifact_title,
				"source_reports": [
					str(value or "").strip()
					for value in (artifact.get("source_reports") or [])
					if str(value or "").strip()
				],
			},
		},
		focused_row=row,
	)
	expansion_guidance = evidence_expansion_user_guidance(expansion_plan)
	if expansion_guidance:
		lines.append("")
		lines.append("Next investigation:")
		lines.append(f"- {expansion_guidance}")
		lines.append(
			f"- For this {section_label.lower()} line, the useful drilldown is source detail that explains which transactions, items, suppliers, or timing movements created the amount."
		)
	lines.append("")
	lines.append("This is based only on the result above.")
	return "\n".join(lines).strip()


def _section_insight_rows(rows: List[Dict[str, Any]], total_value: Any) -> List[Dict[str, Any]]:
	total_number = abs(_numeric(total_value))
	if len(rows) <= 1 or total_number <= 0.0001:
		return rows
	# Some ERP reports include both a section total row and child rows in the
	# same section. Use non-total rows for insight percentages to avoid double
	# counting hierarchy totals while still rendering the full table below.
	non_total_rows = [
		row
		for row in rows
		if abs(abs(_numeric(row.get("amount"))) - total_number) > max(0.01, total_number * 0.0001)
	]
	return non_total_rows or rows


def _section_insight_lines(section_label: str, rows: List[Dict[str, Any]], total_value: Any, currency: str) -> List[str]:
	if not rows:
		return []
	total_number = _numeric(total_value)
	insight_rows = _section_insight_rows(rows, total_value)
	largest = insight_rows[0]
	largest_label = _row_label(largest)
	largest_amount = _numeric(largest.get("amount"))
	lines: List[str] = []
	if largest_label and abs(largest_amount) > 0.0001:
		if abs(total_number) > 0.0001:
			lines.append(
				f"- Largest line: {largest_label} at {_money(largest_amount)} {currency}, "
				f"or {abs(largest_amount) / abs(total_number) * 100:.1f}% of {section_label.lower()}."
			)
		else:
			lines.append(f"- Largest line: {largest_label} at {_money(largest_amount)} {currency}.")
	if len(insight_rows) > 1 and abs(total_number) > 0.0001:
		top_sum = sum(abs(_numeric(row.get("amount"))) for row in insight_rows[:3])
		if top_sum <= abs(total_number) * 1.05:
			lines.append(
				f"- Top displayed lines represent {top_sum / abs(total_number) * 100:.1f}% of {section_label.lower()}."
			)
	return lines


def artifact_section_detail_direct_evidence_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	currency = str(dimensions.get("currency") or "MMK").strip() or "MMK"
	line_section_key, line_row = _artifact_line_from_message(raw_message, artifact)
	if line_section_key and line_row:
		line_answer = _line_item_detail_answer(
			section_key=line_section_key,
			row=line_row,
			artifact=artifact,
			currency=currency,
		)
		if line_answer:
			return line_answer
	section_key = _artifact_section_from_message(raw_message, artifact)
	if not section_key:
		return ""
	section_label = _section_label(section_key)
	artifact_title = _artifact_title(artifact)
	total_value = _metric_total_for_section(section_key, artifact)
	rows = _section_rows(section_key, artifact)
	lines: List[str] = []
	if total_value not in (None, ""):
		lines.append(f"{section_label} in the current {artifact_title} total {_money(total_value)} {currency}.")
	else:
		lines.append(f"{section_label} in the current {artifact_title}:")
	insights = _section_insight_lines(section_label, rows, total_value, currency)
	if insights:
		lines.append("")
		lines.append("Key insights from the visible data:")
		lines.extend(insights)
	if rows:
		columns = _section_row_columns(rows)
		lines.append("")
		lines.append(f"{section_label} Lines")
		lines.append("| " + " | ".join(_human_column_label(column) for column in columns) + " |")
		lines.append("| " + " | ".join("---" for _ in columns) + " |")
		for row in rows:
			lines.append("| " + " | ".join(_format_section_cell(column, row.get(column), currency) for column in columns) + " |")
	lines.append("")
	lines.append("This is based only on the result above.")
	return "\n".join(lines).strip()


def financial_statement_section_direct_evidence_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	if str(artifact.get("family_id") or "").strip() != "financial_statement":
		return ""
	return artifact_section_detail_direct_evidence_answer(
		raw_message=raw_message,
		artifact_payload=artifact,
	)


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


def _ensure_entity_detail_evidence_request_contract(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	evidence_request_contract: Dict[str, Any] | None,
) -> Dict[str, Any]:
	if isinstance(evidence_request_contract, dict):
		return dict(evidence_request_contract)
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	return build_entity_detail_evidence_request_contract(
		request_id=str(artifact.get("request_id") or "").strip(),
		raw_message=raw_message,
		artifact_payload=artifact,
	).to_payload()


def build_grounded_artifact_direct_evidence_rendered_payload(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
	evidence_request_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	stock_payload = item_stock_direct_evidence_rendered_payload(
		raw_message=raw_message,
		artifact_payload=artifact,
		evidence_request_contract=evidence_request_contract,
	)
	if stock_payload:
		return stock_payload
	composite_payload = composite_ranked_row_direct_evidence_rendered_payload(
		raw_message=raw_message,
		artifact_payload=artifact,
		grounded_turn=grounded_turn,
	)
	if composite_payload:
		return composite_payload
	family_id = str(artifact.get("family_id") or "").strip()
	if family_id not in {"entity_detail", "inventory_snapshot"}:
		return {}
	if family_id != "entity_detail":
		return {}
	typed_request = _ensure_entity_detail_evidence_request_contract(
		raw_message=raw_message,
		artifact_payload=artifact,
		evidence_request_contract=evidence_request_contract,
	)
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	entity_type = str(dimensions.get("entity_type") or "").strip().lower()
	entity_question_type = str(typed_request.get("entity_question_type") or "").strip()
	clarification_required = bool(typed_request.get("clarification_required"))
	clarification_reason_type = str(typed_request.get("clarification_reason_type") or "").strip()
	if entity_type == "purchase_order":
		requested_dimensions = set(
			str(value or "").strip()
			for value in (typed_request.get("requested_dimensions") or [])
			if str(value or "").strip()
		)
		requested_metrics = set(
			str(value or "").strip()
			for value in (typed_request.get("requested_metrics") or [])
			if str(value or "").strip()
		)
		if entity_question_type == "purchase_order_actual_receipt_event_date":
			return {}
		if not requested_dimensions.intersection({"document_status", "planned_receipt_date"}) and not requested_metrics.intersection(
			{"receipt_progress_percent", "billing_progress_percent"}
		):
			return {}
		document_row = _artifact_document_row(artifact)
		item_rows = _artifact_item_rows(artifact)
		entity_label = str(dimensions.get("entity_label") or dimensions.get("entity_key") or "Purchase Order").strip()
		supplier = str(document_row.get("supplier") or "").strip()
		status = str(document_row.get("status") or "").strip()
		receipt_status = str(document_row.get("receipt_status") or "").strip()
		billing_status = str(document_row.get("billing_status") or "").strip()
		planned_receipt_date = str(document_row.get("schedule_date") or "").strip()
		per_received = _numeric(document_row.get("per_received"))
		per_billed = _numeric(document_row.get("per_billed"))
		total_qty = _numeric(document_row.get("quantity"))
		received_qty = sum(_numeric(row.get("received_qty")) for row in item_rows)
		billed_amount = sum(_numeric(row.get("billed_amount")) for row in item_rows)
		evidence_rows = [
			["Purchase Order", entity_label],
			["Supplier", supplier],
			["Current Status", status],
			["Receipt Status", receipt_status],
			["Billing Status", billing_status],
			["Planned Receipt Date", planned_receipt_date],
			["Received (%)", _money(per_received)],
			["Billed (%)", _money(per_billed)],
		]
		evidence_items: List[str] = []
		if "document_status" in requested_dimensions:
			evidence_items.append(
				f"The current purchase order status is {status}, with receipt status {receipt_status or 'Unknown'} and billing status {billing_status or 'Unknown'}."
			)
		if "planned_receipt_date" in requested_dimensions and planned_receipt_date:
			evidence_items.append(f"The planned receipt date recorded on the purchase order is {planned_receipt_date}.")
		if "receipt_progress_percent" in requested_metrics:
			receipt_item = f"Receipt progress is {_money(per_received)}%"
			if receipt_status:
				receipt_item += f" ({receipt_status})"
			if total_qty > 0:
				receipt_item += f", with {_money(received_qty)} of {_money(total_qty)} units received on the current order lines"
			evidence_items.append(receipt_item + ".")
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
				_money(row.get("received_qty")),
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
					["Item Code", "Item Name", "Qty", "Received Qty", "Billed Amount (MMK)"],
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
	if entity_type == "sales_order":
		requested_dimensions = set(
			str(value or "").strip()
			for value in (typed_request.get("requested_dimensions") or [])
			if str(value or "").strip()
		)
		requested_metrics = set(
			str(value or "").strip()
			for value in (typed_request.get("requested_metrics") or [])
			if str(value or "").strip()
		)
		if entity_question_type == "sales_order_actual_delivery_event_date":
			return {}
		if not requested_dimensions.intersection({"document_status", "planned_delivery_date"}) and not requested_metrics.intersection(
			{"delivery_progress_percent", "billing_progress_percent"}
		):
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
		if "delivery_progress_percent" in requested_metrics:
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
	evidence_request_contract: Dict[str, Any] | None = None,
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	stock_answer = item_stock_direct_evidence_answer(
		raw_message=raw_message,
		artifact_payload=artifact,
		evidence_request_contract=evidence_request_contract,
	)
	if stock_answer:
		return stock_answer
	composite_answer = composite_ranked_row_direct_evidence_answer(
		raw_message=raw_message,
		artifact_payload=artifact,
		grounded_turn=grounded_turn,
	)
	if composite_answer:
		return composite_answer
	composite_boundary = composite_ranked_row_evidence_boundary_answer(
		raw_message=raw_message,
		artifact_payload=artifact,
		grounded_turn=grounded_turn,
	)
	if composite_boundary:
		return composite_boundary
	statement_section_answer = financial_statement_section_direct_evidence_answer(
		raw_message=raw_message,
		artifact_payload=artifact,
	)
	if statement_section_answer:
		return statement_section_answer
	family_id = str(artifact.get("family_id") or "").strip()
	if family_id not in {"entity_detail", "inventory_snapshot"}:
		return ""
	if family_id != "entity_detail":
		return ""
	typed_request = _ensure_entity_detail_evidence_request_contract(
		raw_message=raw_message,
		artifact_payload=artifact,
		evidence_request_contract=evidence_request_contract,
	)
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	entity_type = str(dimensions.get("entity_type") or "").strip().lower()
	entity_question_type = str(typed_request.get("entity_question_type") or "").strip()
	clarification_required = bool(typed_request.get("clarification_required"))
	clarification_reason_type = str(typed_request.get("clarification_reason_type") or "").strip()
	if entity_type == "purchase_order":
		requested_dimensions = set(
			str(value or "").strip()
			for value in (typed_request.get("requested_dimensions") or [])
			if str(value or "").strip()
		)
		requested_metrics = set(
			str(value or "").strip()
			for value in (typed_request.get("requested_metrics") or [])
			if str(value or "").strip()
		)
		if entity_question_type == "purchase_order_actual_receipt_event_date":
			return ""
		if not requested_dimensions.intersection({"document_status", "planned_receipt_date"}) and not requested_metrics.intersection(
			{"receipt_progress_percent", "billing_progress_percent"}
		):
			return ""
		document_row = _artifact_document_row(artifact)
		item_rows = _artifact_item_rows(artifact)
		entity_label = str(dimensions.get("entity_label") or dimensions.get("entity_key") or "this purchase order").strip()
		status = str(document_row.get("status") or "").strip()
		receipt_status = str(document_row.get("receipt_status") or "").strip()
		billing_status = str(document_row.get("billing_status") or "").strip()
		planned_receipt_date = str(document_row.get("schedule_date") or "").strip()
		per_received = _numeric(document_row.get("per_received"))
		per_billed = _numeric(document_row.get("per_billed"))
		total_qty = _numeric(document_row.get("quantity"))
		received_qty = sum(_numeric(row.get("received_qty")) for row in item_rows)
		billed_amount = sum(_numeric(row.get("billed_amount")) for row in item_rows)
		if "planned_receipt_date" in requested_dimensions and planned_receipt_date:
			return f"The planned receipt date for {entity_label} is {planned_receipt_date}."
		if "billing_progress_percent" in requested_metrics:
			if per_billed >= 100:
				return (
					f"Yes. {entity_label} is fully billed.\n\n"
					f"Billing progress is {_money(per_billed)}% ({billing_status or 'Fully Billed'})."
				)
			if per_billed <= 0:
				return (
					f"No. {entity_label} has not been billed yet.\n\n"
					f"Billing progress is {_money(per_billed)}% ({billing_status or 'Not Billed'})."
				)
			detail = f"It is {_money(per_billed)}% billed so far"
			if billed_amount > 0:
				detail += f", which is {_money(billed_amount)} MMK on the current order lines"
			return f"Partly. {entity_label} is not fully billed yet.\n\n{detail} ({billing_status or 'Partly Billed'})."
		if "document_status" in requested_dimensions and entity_question_type == "purchase_order_document_status":
			return (
				f"The current status of {entity_label} is {status}.\n\n"
				f"Receipt status is {receipt_status or 'Unknown'}, and billing status is {billing_status or 'Unknown'}."
			)
		if "receipt_progress_percent" in requested_metrics:
			if per_received >= 100:
				return (
					f"Yes. {entity_label} is fully received.\n\n"
					f"Receipt progress is {_money(per_received)}% ({receipt_status or 'Fully Received'})."
				)
			if per_received <= 0:
				return (
					f"No. {entity_label} has not been received yet.\n\n"
					f"Receipt progress is {_money(per_received)}% ({receipt_status or 'Not Received'})."
				)
			detail = f"It is {_money(per_received)}% received so far"
			if total_qty > 0:
				detail += f", with {_money(received_qty)} of {_money(total_qty)} units received on the current order lines"
			return f"Partly. {entity_label} is not fully received yet.\n\n{detail} ({receipt_status or 'Partly Received'})."
		return ""
	if entity_type == "sales_order":
		requested_dimensions = set(
			str(value or "").strip()
			for value in (typed_request.get("requested_dimensions") or [])
			if str(value or "").strip()
		)
		requested_metrics = set(
			str(value or "").strip()
			for value in (typed_request.get("requested_metrics") or [])
			if str(value or "").strip()
		)
		if entity_question_type == "sales_order_actual_delivery_event_date":
			return ""
		if not requested_dimensions.intersection({"document_status", "planned_delivery_date"}) and not requested_metrics.intersection(
			{"delivery_progress_percent", "billing_progress_percent"}
		):
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
		if "document_status" in requested_dimensions and entity_question_type == "sales_order_document_status":
			return (
				f"The current status of {entity_label}{customer_phrase} is {status}.\n\n"
				f"Delivery status is {delivery_status or 'Unknown'}, and billing status is {billing_status or 'Unknown'}."
			)
		if "delivery_progress_percent" in requested_metrics:
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
	if entity_type == "customer":
		return customer_boundary_direct_evidence_answer(
			typed_request=typed_request,
			artifact=artifact,
			dimensions=dimensions,
			clarification_required=clarification_required,
			clarification_reason_type=clarification_reason_type,
		)
	if entity_type == "supplier":
		return supplier_boundary_direct_evidence_answer(
			typed_request=typed_request,
			artifact=artifact,
			dimensions=dimensions,
		)
	if entity_question_type not in {"sales_invoice_delivery_evidence", "sales_invoice_delivery_event_date"}:
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
	requested_dimensions = set(
		str(value or "").strip()
		for value in (typed_request.get("requested_dimensions") or [])
		if str(value or "").strip()
	)
	wants_posting_date = entity_question_type == "sales_invoice_delivery_event_date" or "posting_date" in requested_dimensions
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
	evidence_request_contract: Dict[str, Any] | None = None,
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	stock_boundary = item_stock_evidence_boundary_answer(
		raw_message=raw_message,
		artifact_payload=artifact,
		evidence_request_contract=evidence_request_contract,
	)
	if stock_boundary:
		return stock_boundary
	composite_boundary = composite_ranked_row_evidence_boundary_answer(
		raw_message=raw_message,
		artifact_payload=artifact,
		grounded_turn=grounded_turn,
	)
	if composite_boundary:
		return composite_boundary
	if str(artifact.get("family_id") or "").strip() not in {"entity_detail", "transaction_listing", "inventory_snapshot"}:
		return ""
	entity_type = ""
	if isinstance(artifact.get("dimensions"), dict):
		entity_type = str((artifact.get("dimensions") or {}).get("entity_type") or "").strip().lower()
	if str(artifact.get("family_id") or "").strip() == "entity_detail":
		typed_request = _ensure_entity_detail_evidence_request_contract(
			raw_message=raw_message,
			artifact_payload=artifact,
			evidence_request_contract=evidence_request_contract,
		)
		entity_question_type = str(typed_request.get("entity_question_type") or "").strip()
		if entity_type == "purchase_order" and entity_question_type == "purchase_order_actual_receipt_event_date":
			return (
				"The current purchase order shows planned receipt date and receipt progress, but it does not prove the actual receipt event date.\n\n"
				"To answer when it was actually received, I need linked downstream receipt evidence such as purchase-receipt records."
			)
		if entity_type == "sales_order" and entity_question_type == "sales_order_actual_delivery_event_date":
			return (
				"The current sales order shows planned delivery date and delivery progress, but it does not prove the actual shipment event date.\n\n"
				"To answer when it was actually delivered, I need linked downstream fulfillment evidence such as delivery-note records."
			)
		if entity_type == "sales_invoice" and entity_question_type in {"sales_invoice_delivery_evidence", "sales_invoice_delivery_event_date"}:
			evidence_concepts = artifact_evidence_concepts(artifact, grounded_turn)
			if "fulfillment" not in evidence_concepts:
				return (
					"The answer above does not include direct fields proving fulfillment status, so I can't confirm it confidently from that answer alone.\n\n"
					"I can confirm the billing and payment fields shown here, but this question needs operational evidence such as delivery or stock-movement records."
				)
		return ""
	if entity_type == "purchase_order":
		requested_dimensions = set(
			detect_canonical_keys(
				raw_message,
				capability_id="purchase_order_read",
				dimension_or_metric="dimension",
			)
		)
		if "posting_date" in requested_dimensions and "planned_receipt_date" not in requested_dimensions:
			return (
				"The current purchase order shows planned receipt date and receipt progress, but it does not prove the actual receipt event date.\n\n"
				"To answer when it was actually received, I need linked downstream receipt evidence such as purchase-receipt records."
			)
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
				"To answer when it was actually delivered, I need linked downstream fulfillment evidence such as delivery-note records."
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
		"The answer above does not include direct fields proving "
		f"{concept_label} status, so I can't confirm it confidently from that answer alone.\n\n"
		"I can confirm the billing and payment fields shown here, but this question needs operational evidence such as "
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

	requested_targets = list(requested_columns or ([target_metric] if target_metric else []))
	raw_requested = [value for value in requested_targets if value]
	base_metric_label = _label_for(target_metric) if target_metric else ""
	source_report = str(getattr(compatibility_contract, "source_report", "") or "").strip()
	report_basis = source_report or "the current ERP report"
	if raw_requested:
		return (
			f"The current {report_basis} result does not include the deeper supporting detail needed for that breakdown.\n\n"
			"I can summarize the facts already shown, but I should not invent source rows, transactions, or item-level detail from a summary line. "
			"Ask for the relevant detail or source view behind this line if you want the breakdown."
		)
	if base_metric_label:
		return (
			f"The current {report_basis} result does not include enough supporting detail to switch this answer to {base_metric_label} accurately.\n\n"
			"I can summarize the facts already shown, but I should not invent a metric that is not present in the current result. "
			"Ask for the report or detail view that contains that metric if you want me to calculate or compare it."
		)
	return (
		f"The current {report_basis} result does not include enough supporting detail for that deeper view.\n\n"
		"I can summarize the facts already shown, but I should not invent missing detail. Ask for the relevant detail or source view if you want a fuller breakdown."
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
