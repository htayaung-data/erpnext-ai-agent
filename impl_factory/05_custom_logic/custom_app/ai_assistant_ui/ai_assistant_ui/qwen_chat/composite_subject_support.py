from __future__ import annotations

from typing import Any, Tuple

from ai_assistant_ui.qwen_chat.item_product_support import (
	is_item_product_grain,
	item_product_subject_label,
)


def _normalized_key(value: Any) -> str:
	return str(value or "").strip().lower().replace(" ", "_")


def composite_family_from_entity_dimension(entity_dimension: Any) -> Tuple[str, str]:
	key = _normalized_key(entity_dimension)
	if key == "customer":
		return "customer_commercial_ranking", "customer"
	if is_item_product_grain(key):
		return "product_commercial_ranking", "product"
	return "", ""


def composite_entity_dimension_label(entity_grain: Any) -> str:
	value = _normalized_key(entity_grain)
	if value == "customer":
		return "Customer"
	if is_item_product_grain(value):
		return item_product_subject_label(value, analytical=True)
	return str(entity_grain or "").strip().title() or "Entity"
