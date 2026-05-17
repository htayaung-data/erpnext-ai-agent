from __future__ import annotations

from typing import Any, Dict, Tuple


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def transaction_party_label(row: Dict[str, Any]) -> str:
	return _clean_text(row.get("customer") or row.get("party_name") or row.get("party"))


def ranked_entity_key_label(row: Dict[str, Any]) -> Tuple[str, str]:
	label = _clean_text(row.get("entity_name") or row.get("entity"))
	key = _clean_text(row.get("entity_code") or row.get("entity") or row.get("entity_name"))
	return key, label


def master_data_entity_key_label(row: Dict[str, Any]) -> Tuple[str, str]:
	key = _clean_text(
		row.get("entity_code")
		or row.get("customer_code")
		or row.get("supplier_code")
		or row.get("item_code")
		or row.get("entity")
		or row.get("entity_name")
		or row.get("customer_name")
		or row.get("supplier_name")
		or row.get("item_name")
		or row.get("customer")
		or row.get("supplier")
		or row.get("item")
	)
	label = _clean_text(
		row.get("entity_name")
		or row.get("entity")
		or row.get("customer_name")
		or row.get("supplier_name")
		or row.get("item_name")
		or row.get("customer")
		or row.get("supplier")
		or row.get("item")
	)
	return key, label
