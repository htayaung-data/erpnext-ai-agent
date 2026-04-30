from __future__ import annotations

from typing import Dict, Iterable, List

from ai_assistant_ui.qwen_chat.metadata import (
	entity_grain_display_label,
	get_report_spec,
)


def requested_master_directory_columns(
	*,
	requested_dimensions: Iterable[str],
	lookup_projection: str,
	entity_type: str,
) -> List[str]:
	requested = {
		str(value or "").strip()
		for value in requested_dimensions
		if str(value or "").strip()
	}
	columns: List[str] = []
	if entity_type in requested or "party" in requested:
		columns.append("entity")
	if entity_type == "customer":
		if "territory" in requested:
			columns.append("region")
		if "customer_group" in requested:
			columns.append("group")
	else:
		if "country" in requested:
			columns.append("region")
		if "supplier_group" in requested:
			columns.append("group")
	if "creation" in requested:
		columns.append("creation")
	if "status" in requested:
		columns.append("status")
	if "default_price_list" in requested:
		columns.append("default_price_list")
	if "payment_terms" in requested:
		columns.append("payment_terms")
	columns = list(dict.fromkeys([value for value in columns if value]))
	if columns == ["entity"] and lookup_projection == "standard_directory":
		return []
	if not columns and lookup_projection in {"", "names_only"}:
		return ["entity"]
	return columns


def master_directory_requested_column_alias_map(entity_type: str) -> Dict[str, str]:
	aliases: Dict[str, str] = {
		"entity": "entity",
		"name": "entity",
		"customer": "entity",
		"customer_name": "entity",
		"supplier": "entity",
		"supplier_name": "entity",
		"item": "entity",
		"item_name": "entity",
		"product": "entity",
		"product_name": "entity",
		"region": "region",
		"territory": "region",
		"country": "region",
		"brand": "region",
		"group": "group",
		"customer_group": "group",
		"supplier_group": "group",
		"item_group": "group",
		"creation": "creation",
		"created_date": "creation",
		"status": "status",
		"default_price_list": "default_price_list",
		"payment_terms": "payment_terms",
	}
	entity_key = str(entity_type or "").strip().lower()
	if entity_key == "customer":
		aliases["that_customer"] = "entity"
	elif entity_key == "supplier":
		aliases["that_supplier"] = "entity"
	elif entity_key == "item":
		aliases["that_item"] = "entity"
		aliases["that_product"] = "entity"
	return aliases


def master_directory_context(report_name: str) -> Dict[str, str]:
	report_spec = get_report_spec(report_name)
	direct_query = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	doctype = str(direct_query.get("doctype") or "").strip()
	if doctype == "Item":
		return {
			"entity_type": "item",
			"entity_label": entity_grain_display_label("item", plural=False).title() or "Item",
			"entity_plural_label": entity_grain_display_label("item", plural=True).title() or "Items",
			"name_field": "item_name",
			"group_field": "item_group",
			"region_field": "brand",
			"region_label": "Brand",
			"group_label": "Item Group",
			"source_grain": "item_master_list",
		}
	if doctype == "Supplier":
		return {
			"entity_type": "supplier",
			"entity_label": entity_grain_display_label("supplier", plural=False).title() or "Supplier",
			"entity_plural_label": entity_grain_display_label("supplier", plural=True).title() or "Suppliers",
			"name_field": "supplier_name",
			"group_field": "supplier_group",
			"region_field": "country",
			"region_label": "Country",
			"group_label": "Supplier Group",
			"source_grain": "supplier_master_list",
		}
	return {
		"entity_type": "customer",
		"entity_label": entity_grain_display_label("customer", plural=False).title() or "Customer",
		"entity_plural_label": entity_grain_display_label("customer", plural=True).title() or "Customers",
		"name_field": "customer_name",
		"group_field": "customer_group",
		"region_field": "territory",
		"region_label": "Territory",
		"group_label": "Customer Group",
		"source_grain": "customer_master_list",
	}
