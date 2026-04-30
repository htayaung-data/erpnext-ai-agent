from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def composite_row_join_key_value(row: Dict[str, Any], key: str) -> str:
	clean_key = _clean_text(key)
	if clean_key == "customer":
		return _clean_text(row.get("customer") or row.get("entity_key"))
	if clean_key == "item_code":
		return _clean_text(row.get("item_code") or row.get("entity_code") or row.get("entity_key"))
	return _clean_text(row.get(clean_key))


def composite_row_join_key_tuple(row: Dict[str, Any], join_key_schema: List[str]) -> Tuple[str, ...]:
	return tuple(composite_row_join_key_value(row, key) for key in join_key_schema)


def composite_row_join_key_payload(row: Dict[str, Any], join_key_schema: List[str]) -> Dict[str, Any]:
	return {
		key: composite_row_join_key_value(row, key)
		for key in join_key_schema
		if composite_row_join_key_value(row, key)
	}


def composite_row_identity_value(row: Dict[str, Any], row_identity_policy: str) -> str:
	policy = _clean_text(row_identity_policy)
	if policy == "item_name_prefer_code":
		return _clean_text(row.get("item_name") or row.get("entity_name") or row.get("item_code") or row.get("entity_code"))
	if policy == "item_code":
		return _clean_text(row.get("item_code") or row.get("entity_code"))
	return _clean_text(row.get("customer_name") or row.get("entity_name") or row.get("customer"))


def composite_row_entity_code(row: Dict[str, Any]) -> str:
	return _clean_text(row.get("entity_code") or row.get("item_code") or row.get("customer"))


def composite_join_key_label(entity_grain: str) -> str:
	return "item_code" if _clean_text(entity_grain) == "item" else "customer"
