from __future__ import annotations

from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys


def entity_type_from_dimension(value: str, *, include_documents: bool = False) -> str:
	dimension_keys = detect_canonical_keys(str(value or ""), dimension_or_metric="dimension")
	for key in dimension_keys:
		if key == "supplier":
			return "supplier"
		if key == "customer":
			return "customer"
		if key in {"item_code", "item_name"}:
			return "item"
		if include_documents and key == "document_name":
			return "sales_invoice"
	return ""
