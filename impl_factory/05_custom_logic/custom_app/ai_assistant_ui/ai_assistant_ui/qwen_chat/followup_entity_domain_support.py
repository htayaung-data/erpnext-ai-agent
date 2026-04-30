from __future__ import annotations

from typing import Dict, List, Set

from ai_assistant_ui.qwen_chat.item_product_support import (
	is_item_product_grain,
	item_product_context_domains,
	normalize_item_product_grain,
)
from ai_assistant_ui.qwen_chat.metadata import (
	list_composite_family_specs,
	ontology_detect_concepts,
)


_GOVERNED_DOMAIN_CONCEPTS = {
	"payable",
	"receivable",
	"sales",
	"product",
	"inventory",
	"supplier",
	"customer",
}


def _normalize_text(text: str) -> str:
	return " ".join(str(text or "").strip().lower().split())


def _singularize_token(token: str) -> str:
	clean = str(token or "").strip().lower()
	if len(clean) > 4 and clean.endswith("ies"):
		return clean[:-3] + "y"
	if len(clean) > 3 and clean.endswith("ses"):
		return clean[:-2]
	if len(clean) > 3 and clean.endswith("s") and not clean.endswith("ss"):
		return clean[:-1]
	return clean


def _normalize_slot_phrase(text: str) -> str:
	parts = [
		_singularize_token(value)
		for value in str(text or "").strip().lower().replace("/", " ").split()
		if _singularize_token(value)
	]
	return " ".join(parts)


def normalize_entity_grain_alias(value: str) -> str:
	return normalize_item_product_grain(_normalize_text(str(value or "").replace("_", " ")))


def _pluralize_subject_alias(value: str) -> str:
	clean = str(value or "").strip().lower()
	if not clean:
		return ""
	if clean.endswith("y") and len(clean) > 1 and clean[-2] not in "aeiou":
		return clean[:-1] + "ies"
	if clean.endswith(("s", "x", "z", "ch", "sh")):
		return clean + "es"
	return clean + "s"


def ranking_subject_alias_map() -> Dict[str, str]:
	out: Dict[str, str] = {}
	for family_spec in list_composite_family_specs():
		subject_alias = str(family_spec.get("subject_alias_value") or "").strip().lower()
		if not subject_alias:
			continue
		alias_values = {
			_normalize_slot_phrase(subject_alias),
			_normalize_slot_phrase(_pluralize_subject_alias(subject_alias)),
		}
		entity_grain = str(family_spec.get("entity_grain") or "").strip().lower()
		if entity_grain == "item":
			alias_values.update(
				{
					_normalize_slot_phrase("item"),
					_normalize_slot_phrase("items"),
				}
			)
		for alias_value in alias_values:
			if alias_value:
				out[alias_value] = subject_alias
	return out


def subject_alias_from_label(label: str) -> str:
	normalized_label = _normalize_slot_phrase(label)
	if not normalized_label:
		return ""
	alias_map = ranking_subject_alias_map()
	resolved = alias_map.get(normalized_label)
	if resolved:
		return resolved
	if is_item_product_grain(normalized_label):
		return "product"
	return ""


def local_entity_detail_followup_family_ids() -> Set[str]:
	out: Set[str] = set()
	for family_spec in list_composite_family_specs():
		local_family_id = str(family_spec.get("local_followup_family_id") or "").strip()
		if not local_family_id:
			continue
		entity_grain = normalize_entity_grain_alias(str(family_spec.get("entity_grain") or "").strip())
		subject_alias = subject_alias_from_label(str(family_spec.get("subject_alias_value") or "").strip())
		detail_affordances = {
			f"{value}_detail"
			for value in {entity_grain, subject_alias}
			if value
		}
		if not detail_affordances:
			continue
		declared_affordances = {
			str(value or "").strip()
			for value in (family_spec.get("followup_affordances") or [])
			if str(value or "").strip()
		}
		if declared_affordances.intersection(detail_affordances):
			out.add(local_family_id)
	return out


def is_entity_detail_context_family(
	family_id: str,
	grounded_turn: Dict[str, object] | None = None,
) -> bool:
	clean_family_id = str(family_id or "").strip()
	if clean_family_id == "entity_detail":
		return True
	if clean_family_id not in local_entity_detail_followup_family_ids():
		return False
	if grounded_turn is None:
		return True
	return bool(entity_detail_context_domains(grounded_turn))


def entity_detail_context_domains(grounded_turn: Dict[str, object] | None) -> Set[str]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	out: Set[str] = set()
	for item in (turn.get("known_entities") or []):
		if not isinstance(item, dict):
			continue
		entity_type = str(item.get("entity_type") or "").strip().lower()
		if entity_type in _GOVERNED_DOMAIN_CONCEPTS:
			out.add(entity_type)
		else:
			out.update(item_product_context_domains(entity_type))
	for value in (turn.get("dimensions") or []):
		resolved = subject_alias_from_label(str(value or "").strip())
		if resolved:
			out.add(resolved)
		if str(value or "").strip().lower() == "customer":
			out.add("customer")
	return out


def detected_message_entity_domains(message: str) -> Set[str]:
	return {
		normalize_entity_grain_alias(value)
		for value in ontology_detect_concepts(message, include_extended=False)
		if normalize_entity_grain_alias(value) in {"customer", "supplier", "item", "inventory"}
	}
