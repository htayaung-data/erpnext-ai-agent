from __future__ import annotations

from typing import Any, Dict, List

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None

from ai_assistant_ui.qwen_chat.metadata import get_report_spec


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _safe_sql_identifier(value: Any) -> str:
	clean = _clean_text(value)
	if not clean:
		raise ValueError("Governed SQL identifier is required.")
	import re

	if not re.fullmatch(r"[A-Za-z0-9_ ]+", clean):
		raise ValueError(f"Unsupported governed SQL identifier: {value!r}")
	return clean


def _as_str_list(value: Any) -> List[str]:
	if not isinstance(value, list):
		return []
	out: List[str] = []
	for item in value:
		text = _clean_text(item)
		if text:
			out.append(text)
	return out


def _governed_period_grouping_spec(report_name: str) -> Dict[str, Any]:
	report_spec = get_report_spec(report_name)
	direct_query = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	grouping = report_spec.get("governed_period_grouping") if isinstance(report_spec.get("governed_period_grouping"), dict) else {}
	if not direct_query or not grouping:
		return {}
	doctype = _clean_text(direct_query.get("doctype"))
	if not doctype:
		return {}
	entity_grain = _clean_text(grouping.get("entity_grain"))
	entity_key_fields = _as_str_list(grouping.get("entity_key_fields"))
	entity_label_fields = _as_str_list(grouping.get("entity_label_fields"))
	document_key_field = _clean_text(grouping.get("document_key_field"))
	revenue_field = _clean_text(grouping.get("revenue_field"))
	quantity_field = _clean_text(grouping.get("quantity_field"))
	if not entity_grain or not entity_key_fields or not entity_label_fields or not document_key_field or not revenue_field or not quantity_field:
		return {}
	parent_join = direct_query.get("parent_join") if isinstance(direct_query.get("parent_join"), dict) else {}
	if parent_join:
		parent_doctype = _clean_text(parent_join.get("doctype"))
		child_link_field = _clean_text(parent_join.get("child_link_field"))
		date_field = _clean_text(parent_join.get("date_field"))
		company_field = _clean_text(parent_join.get("company_field") or "company")
		if not parent_doctype or not child_link_field or not date_field:
			return {}
		return {
			"doctype": doctype,
			"entity_grain": entity_grain,
			"entity_key_fields": entity_key_fields,
			"entity_label_fields": entity_label_fields,
			"entity_code_field": _clean_text(grouping.get("entity_code_field")),
			"document_key_field": document_key_field,
			"revenue_field": revenue_field,
			"quantity_field": quantity_field,
			"date_field": date_field,
			"company_field": company_field,
			"fixed_filters": dict(parent_join.get("fixed_filters") or {}),
			"parent_doctype": parent_doctype,
			"child_link_field": child_link_field,
		}
	date_field = _clean_text(direct_query.get("date_field"))
	if not date_field:
		return {}
	return {
		"doctype": doctype,
		"entity_grain": entity_grain,
		"entity_key_fields": entity_key_fields,
		"entity_label_fields": entity_label_fields,
		"entity_code_field": _clean_text(grouping.get("entity_code_field")),
		"document_key_field": document_key_field,
		"revenue_field": revenue_field,
		"quantity_field": quantity_field,
		"date_field": date_field,
		"company_field": _clean_text(direct_query.get("company_field") or "company"),
		"fixed_filters": dict(direct_query.get("fixed_filters") or {}),
	}


def _entity_alias_payload(entity_grain: str, *, entity_key: str, entity_label: str, entity_code: str) -> Dict[str, Any]:
	if entity_grain == "customer":
		return {
			"customer": entity_key,
			"customer_name": entity_label,
		}
	if entity_grain == "item":
		return {
			"item": entity_label or entity_key,
			"item_code": entity_code or entity_key,
			"item_name": entity_label or entity_key,
		}
	return {}


def list_entity_period_commercial_rows(
	*,
	report_name: str,
	company: str,
	from_date: str,
	to_date: str,
) -> List[Dict[str, Any]]:
	if frappe is None:
		return []
	query_spec = _governed_period_grouping_spec(report_name)
	if not query_spec:
		return []

	base_doctype = _safe_sql_identifier(query_spec.get("doctype"))
	date_field = _safe_sql_identifier(query_spec.get("date_field"))
	company_field = _safe_sql_identifier(query_spec.get("company_field") or "company")
	document_key_field = _safe_sql_identifier(query_spec.get("document_key_field"))
	revenue_field = _safe_sql_identifier(query_spec.get("revenue_field"))
	quantity_field = _safe_sql_identifier(query_spec.get("quantity_field"))
	entity_key_fields = [_safe_sql_identifier(value) for value in query_spec.get("entity_key_fields") or []]
	entity_label_fields = [_safe_sql_identifier(value) for value in query_spec.get("entity_label_fields") or []]
	entity_code_field = _clean_text(query_spec.get("entity_code_field"))
	entity_code_identifier = _safe_sql_identifier(entity_code_field) if entity_code_field else ""

	field_order: List[str] = []
	for field_name in [*entity_key_fields, *entity_label_fields, entity_code_identifier]:
		if field_name and field_name not in field_order:
			field_order.append(field_name)

	select_parts = [f"base.`{field_name}` as `{field_name}`" for field_name in field_order]
	group_parts = [f"base.`{field_name}`" for field_name in field_order]

	parent_doctype = _clean_text(query_spec.get("parent_doctype"))
	child_link_field = _clean_text(query_spec.get("child_link_field"))
	parent_join_clause = ""
	parent_alias = "base"
	where_clauses: List[str] = []
	params: List[Any] = []
	if parent_doctype and child_link_field:
		parent_alias = "parent_doc"
		parent_doctype_identifier = _safe_sql_identifier(parent_doctype)
		child_link_identifier = _safe_sql_identifier(child_link_field)
		parent_join_clause = (
			f" inner join `tab{parent_doctype_identifier}` as parent_doc"
			f" on parent_doc.`name` = base.`{child_link_identifier}`"
		)
	for fieldname, value in dict(query_spec.get("fixed_filters") or {}).items():
		clean_fieldname = _safe_sql_identifier(fieldname)
		where_clauses.append(f"{parent_alias}.`{clean_fieldname}` = %s")
		params.append(value)
	where_clauses.append(f"{parent_alias}.`{company_field}` = %s")
	params.append(_clean_text(company))
	where_clauses.append(f"{parent_alias}.`{date_field}` between %s and %s")
	params.extend([_clean_text(from_date), _clean_text(to_date)])

	rows = frappe.db.sql(
		f"""
		select
			{", ".join(select_parts)},
			count(distinct base.`{document_key_field}`) as document_count,
			coalesce(sum(base.`{revenue_field}`), 0) as revenue_total,
			coalesce(sum(base.`{quantity_field}`), 0) as quantity_total
		from `tab{base_doctype}` as base
		{parent_join_clause}
		where {" and ".join(where_clauses)}
		group by {", ".join(group_parts)}
		""",
		tuple(params),
		as_dict=True,
	)

	entity_grain = _clean_text(query_spec.get("entity_grain"))
	out: List[Dict[str, Any]] = []
	for row in (rows or []):
		if not isinstance(row, dict):
			continue
		entity_key = next((_clean_text(row.get(field_name)) for field_name in entity_key_fields if _clean_text(row.get(field_name))), "")
		entity_label = next((_clean_text(row.get(field_name)) for field_name in entity_label_fields if _clean_text(row.get(field_name))), entity_key)
		entity_code = _clean_text(row.get(entity_code_identifier)) if entity_code_identifier else entity_key
		if entity_grain == "item" and not entity_code:
			continue
		if not entity_key:
			continue
		document_count = int(_numeric(row.get("document_count")))
		revenue_total = _numeric(row.get("revenue_total"))
		quantity_total = _numeric(row.get("quantity_total"))
		average_document_value = (revenue_total / float(document_count)) if document_count > 0 else 0.0
		average_unit_price = (revenue_total / float(quantity_total)) if quantity_total > 0 else 0.0
		entry = {
			"entity_grain": entity_grain,
			"entity_key": entity_key,
			"entity_label": entity_label or entity_key,
			"entity_code": entity_code or entity_key,
			"document_count": document_count,
			"revenue_total": revenue_total,
			"quantity_total": quantity_total,
			"average_document_value": average_document_value,
			"average_unit_price": average_unit_price,
			"report_name": _clean_text(report_name),
			"period_start": _clean_text(from_date),
			"period_end": _clean_text(to_date),
		}
		entry.update(
			_entity_alias_payload(
				entity_grain,
				entity_key=entity_key,
				entity_label=entity_label or entity_key,
				entity_code=entity_code or entity_key,
			)
		)
		out.append(entry)
	return out
