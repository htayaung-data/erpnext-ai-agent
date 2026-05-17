from __future__ import annotations

from typing import Any, Set


def _normalized_key(value: Any) -> str:
	return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def normalize_item_product_grain(value: Any) -> str:
	key = _normalized_key(value)
	if key == "product":
		return "item"
	return key


def is_item_product_grain(value: Any) -> bool:
	key = _normalized_key(value)
	return key in {"item", "product"}


def item_product_context_domains(value: Any) -> Set[str]:
	if normalize_item_product_grain(value) == "item":
		return {"product", "inventory"}
	return set()


def item_product_subject_label(value: Any, *, analytical: bool = False) -> str:
	if normalize_item_product_grain(value) == "item":
		return "Product" if analytical else "Item"
	return str(value or "").strip().title() or "Entity"
