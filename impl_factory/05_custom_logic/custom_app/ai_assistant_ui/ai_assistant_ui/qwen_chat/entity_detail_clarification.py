from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.clarification_templates import render_shared_choice_list_clarification
from ai_assistant_ui.qwen_chat.customer_lifecycle_basis import (
	customer_lifecycle_tenure_aliases_by_option,
	customer_lifecycle_tenure_basis_choices,
)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def customer_tenure_basis_choices() -> List[Dict[str, str]]:
	return customer_lifecycle_tenure_basis_choices()


def customer_operational_document_choices() -> List[Dict[str, str]]:
	return [
		{
			"label": "First Sales Order Date",
			"resolved_message": "when was the first sales order for this customer?",
		},
		{
			"label": "First Sales Invoice Date",
			"resolved_message": "when was the first sales invoice for this customer?",
		},
		{
			"label": "Specific Sales Document Detail",
			"resolved_message": "tell me more about a specific sales order or sales invoice for this customer",
		},
	]


def customer_tenure_aliases_by_option() -> Dict[str, List[str]]:
	return customer_lifecycle_tenure_aliases_by_option()


def customer_operational_document_aliases_by_option() -> Dict[str, List[str]]:
	return {
		"First Sales Order Date": [
			"first sales order",
			"sales order date",
			"first order date",
		],
		"First Sales Invoice Date": [
			"first sales invoice",
			"sales invoice date",
			"first invoice date",
		],
		"Specific Sales Document Detail": [
			"specific sales order",
			"specific sales invoice",
			"specific sales document",
			"show the document",
		],
	}


def entity_detail_clarification_signal_spec(
	*,
	reason_type: str,
	entity_label: str,
) -> Dict[str, Any]:
	clean_reason_type = _clean_text(reason_type)
	clean_entity_label = _clean_text(entity_label)
	if clean_reason_type == "customer_tenure_basis_missing":
		choices = customer_tenure_basis_choices()
		suggested_options = [
			_clean_text(item.get("label"))
			for item in choices
			if _clean_text(item.get("label"))
		]
		return {
			"user_question": render_shared_choice_list_clarification(
				reason_type=clean_reason_type,
				variant="default",
				template_values={"entity_label": clean_entity_label},
				options=suggested_options,
				default_question=f"I can calculate customer tenure for {clean_entity_label}, but I need the date basis first.",
			),
			"suggested_options": suggested_options,
			"internal_reason": (
				"Customer tenure is governed, but the evidence request must resolve the approved lifecycle basis before the current "
				"artifact can answer safely."
			),
			"resolved_message_by_option": {
				_clean_text(item.get("label")): _clean_text(item.get("resolved_message"))
				for item in choices
				if _clean_text(item.get("label")) and _clean_text(item.get("resolved_message"))
			},
			"option_aliases_by_option": customer_tenure_aliases_by_option(),
		}
	if clean_reason_type == "customer_operational_document_missing":
		choices = customer_operational_document_choices()
		suggested_options = [
			_clean_text(item.get("label"))
			for item in choices
			if _clean_text(item.get("label"))
		]
		return {
			"user_question": render_shared_choice_list_clarification(
				reason_type=clean_reason_type,
				variant="default",
				template_values={"entity_label": clean_entity_label},
				options=suggested_options,
				default_question=f"I can help with that for {clean_entity_label}, but I need the exact sales document or date basis first.",
			),
			"suggested_options": suggested_options,
			"internal_reason": (
				"The current customer profile does not directly prove operational delivery events, so the request must resolve "
				"to an approved sales lifecycle basis or a specific sales document."
			),
			"resolved_message_by_option": {
				_clean_text(item.get("label")): _clean_text(item.get("resolved_message"))
				for item in choices
				if _clean_text(item.get("label")) and _clean_text(item.get("resolved_message"))
			},
			"option_aliases_by_option": customer_operational_document_aliases_by_option(),
		}
	return {}


def entity_detail_boundary_clarification_answer(
	*,
	reason_type: str,
	entity_label: str,
	company_phrase: str = "",
) -> str:
	clean_reason_type = _clean_text(reason_type)
	clean_entity_label = _clean_text(entity_label)
	clean_company_phrase = _clean_text(company_phrase)
	if clean_company_phrase:
		clean_company_phrase = f" {clean_company_phrase}"
	if clean_reason_type == "customer_operational_document_missing":
		return (
			f"I can help with that for {clean_entity_label}{clean_company_phrase}, but I need the exact sales document or date basis first.\n\n"
			"You can ask for the first sales order date, the first sales invoice date, or details for a specific sales order or sales invoice."
		)
	return ""
