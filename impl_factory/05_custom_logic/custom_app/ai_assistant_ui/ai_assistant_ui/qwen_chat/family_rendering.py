from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	NormalizedFamilyArtifactContract,
	RenderedFamilyResponseContract,
	build_rendered_family_response_contract,
)
from ai_assistant_ui.qwen_chat.governed_scope_registry import scope_id_for_entity_grain
from ai_assistant_ui.qwen_chat.metadata import (
	composite_read_renderer_id,
	financial_statement_report_name,
	get_scope_projection_spec,
	report_family_renderer_id,
)


def _clean_rows(values: Any) -> List[Dict[str, Any]]:
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(item or "").strip() for item in values if str(item or "").strip()]


def _clean_text(value: Any) -> str:
	if value is None:
		return ""
	return str(value).strip()


def _float_value(value: Any) -> float:
	if isinstance(value, (int, float)):
		return float(value)
	text = str(value or "").strip().replace(",", "")
	if not text:
		return 0.0
	try:
		return float(text)
	except Exception:
		return 0.0


def _ratio_text(value: Any) -> str:
	number = _float_value(value)
	if abs(number) <= 1.0:
		number *= 100.0
	return f"{number:.1f}%"


def _amount_text(value: Any, currency: str = "", show_million: bool = False) -> str:
	"""
	Format amount with optional million transformation.
	
	Args:
		value: Numeric value
		currency: Currency label (e.g., "MMK")
		show_million: If True, divide by 1,000,000 and label as "Million {currency}"
	
	Returns:
		Formatted amount string
	"""
	number = _float_value(value)
	
	if show_million:
		# Divide by million and format
		million_value = number / 1_000_000.0
		formatted = f"{million_value:,.2f}".rstrip("0").rstrip(".")
		clean_currency = _clean_text(currency)
		if clean_currency:
			return f"{formatted} Million {clean_currency}"
		return f"{formatted}"
	
	# Normal formatting
	if abs(number - round(number)) < 0.005:
		formatted = f"{number:,.0f}"
	else:
		formatted = f"{number:,.2f}"
	clean_currency = _clean_text(currency)
	if clean_currency:
		return f"{formatted} {clean_currency}".strip()
	return formatted


def _metric_label(metric_key: str, fallback: str = "Value") -> str:
	key = _clean_text(metric_key).lower()
	clean_fallback = _clean_text(fallback)
	if clean_fallback and clean_fallback.lower() not in {"value", "primary metric"}:
		if clean_fallback == clean_fallback.lower():
			return clean_fallback.replace("_", " ").title()
		return clean_fallback
	return {
		"revenue": "Revenue",
		"sales_amount": "Sales Amount",
		"gross_profit": "Gross Profit",
		"gross_profit_percent": "Gross Profit %",
		"buying_amount": "Buying Amount",
		"quantity": "Quantity",
		"average_order_value": "Average Order Value",
		"average_invoice_value": "Average Invoice Value",
		"outstanding_total": "Outstanding Amount",
		"outstanding_amount": "Outstanding Amount",
		"total_due": "Total Amount Due",
		"total_amount": "Total Amount",
		"balance_value": "Balance Value",
		"balance_qty": "Balance Qty",
		"contribution_percent": "Contribution %",
	}.get(key, fallback or "Value")


def _row_has_metric(rows: List[Dict[str, Any]], metric_key: str) -> bool:
	clean_key = _clean_text(metric_key)
	if not clean_key:
		return False
	return any(clean_key in row for row in rows if isinstance(row, dict))


def _resolve_metric_key(rows: List[Dict[str, Any]], preferred_key: str, fallback_key: str) -> str:
	clean_preferred = _clean_text(preferred_key)
	if clean_preferred == "amount":
		for candidate in ("sales_amount", "gross_profit", "buying_amount", "outstanding_total", "total_due", "balance_value"):
			if _row_has_metric(rows, candidate):
				return candidate
	if clean_preferred and _row_has_metric(rows, clean_preferred):
		return clean_preferred
	if _row_has_metric(rows, fallback_key):
		return fallback_key
	return clean_preferred or fallback_key


def _requested_top_n(dimensions: Dict[str, Any], response_overrides: Dict[str, Any] | None, default: int = 10) -> int:
	override_value = (response_overrides or {}).get("top_n")
	if override_value not in (None, ""):
		try:
			return max(1, min(50, int(override_value)))
		except Exception:
			pass
	stored_value = dimensions.get("requested_top_n")
	if stored_value not in (None, ""):
		try:
			return max(1, min(50, int(stored_value)))
		except Exception:
			pass
	return default


def _requested_sort_direction(
	dimensions: Dict[str, Any],
	response_overrides: Dict[str, Any] | None,
	default: str = "desc",
) -> str:
	override_value = _clean_text((response_overrides or {}).get("sort_direction")).lower()
	if override_value in {"asc", "desc"}:
		return override_value
	stored_value = _clean_text(dimensions.get("requested_sort_direction")).lower()
	if stored_value in {"asc", "desc"}:
		return stored_value
	return default


def _requested_columns(dimensions: Dict[str, Any], response_overrides: Dict[str, Any] | None) -> List[str]:
	override_values = _clean_list((response_overrides or {}).get("requested_columns"))
	if override_values:
		values = override_values
	else:
		values = _clean_list(dimensions.get("requested_columns"))
	column_alias_map = (
		{
			_clean_text(key).lower().replace(" ", "_"): _clean_text(value).lower().replace(" ", "_")
			for key, value in (dimensions.get("requested_column_alias_map") or {}).items()
			if _clean_text(key) and _clean_text(value)
		}
		if isinstance(dimensions.get("requested_column_alias_map"), dict)
		else {}
	)
	normalized: List[str] = []
	for value in values:
		key = _clean_text(value).lower().replace(" ", "_")
		if key in column_alias_map:
			normalized.append(column_alias_map[key])
			continue
		if key in {"transaction_date", "posting_date"}:
			normalized.append("posting_date")
		elif key in {"customer", "supplier", "party", "party_name"}:
			normalized.append("party_name")
		elif key in {"status", "document_status"}:
			normalized.append("status")
		else:
			normalized.append(value)
	return list(dict.fromkeys([value for value in normalized if _clean_text(value)]))


def _display_row_count(requested_count: int, displayed_rows: List[Dict[str, Any]]) -> int:
	if displayed_rows:
		return len(displayed_rows)
	return max(0, int(requested_count or 0))


def _normalized_metric_projection_columns(requested_columns: List[str], metric_key: str) -> List[str]:
	normalized: List[str] = []
	for value in requested_columns or []:
		key = metric_key if value == "amount" else value
		clean_key = _clean_text(key)
		if not clean_key:
			continue
		if clean_key not in normalized:
			normalized.append(clean_key)
	return normalized


def _suppress_summary_block(
	dimensions: Dict[str, Any],
	response_overrides: Dict[str, Any] | None,
) -> bool:
	if bool((response_overrides or {}).get("suppress_summary")):
		return True
	if bool(dimensions.get("suppress_summary_by_default")):
		return True
	projection_mode = _clean_text(dimensions.get("requested_projection_mode")).lower()
	return projection_mode == "explicit_selection"


def _preferred_metric_key(
	rows: List[Dict[str, Any]],
	dimensions: Dict[str, Any],
	response_overrides: Dict[str, Any] | None,
) -> str:
	override_key = _clean_text((response_overrides or {}).get("metric_key"))
	stored_key = _clean_text(dimensions.get("requested_metric_key"))
	fallback_key = _clean_text(dimensions.get("primary_metric_key"))
	return _resolve_metric_key(rows, override_key or stored_key, fallback_key)


def _ranking_table_spec(
	*,
	rows: List[Dict[str, Any]],
	entity_label: str,
	metric_key: str,
	metric_label: str,
	requested_columns: List[str],
	show_million: bool = False,
) -> tuple[List[str], List[List[str]]]:
	column_specs: List[tuple[str, str]] = [("Rank", "rank")]
	selected = list(requested_columns or [])
	if not selected:
		selected = ["entity", metric_key]
	if "entity" not in selected and "entity_code" not in selected:
		selected = ["entity"] + selected
	for key in selected:
		if key == "entity":
			column_specs.append((entity_label, "entity"))
		elif key == "entity_code":
			column_specs.append(("Code", "entity_code"))
		elif key == "contribution_percent":
			column_specs.append(("Contribution %", "contribution_percent"))
		else:
			column_specs.append((_metric_label(key, metric_label if key == metric_key else key), key))
	table_rows: List[List[str]] = []
	for index, item in enumerate(rows, start=1):
		out: List[str] = []
		for label, key in column_specs:
			if key == "rank":
				out.append(str(int(_float_value(item.get("rank")) or index)))
			elif key == "entity":
				out.append(_clean_text(item.get("entity_name") or item.get("item_name") or item.get("item") or item.get("entity")))
			elif key == "entity_code":
				out.append(_clean_text(item.get("entity_code") or item.get("item_code")))
			elif key in {"gross_profit_percent", "contribution_percent"}:
				out.append(_ratio_text(item.get(key)))
			else:
				out.append(_amount_text(item.get(key), show_million=show_million))
		table_rows.append(out)
	return [label for label, _ in column_specs], table_rows


def _title_with_period(title: str, period: Dict[str, Any]) -> str:
	from_date = _clean_text((period or {}).get("from_date"))
	to_date = _clean_text((period or {}).get("to_date"))
	if from_date and to_date:
		return f"{title} ({from_date} to {to_date})"
	if to_date:
		return f"{title} as of {to_date}"
	return title


def _period_phrase(period: Dict[str, Any]) -> str:
	from_date = _clean_text((period or {}).get("from_date"))
	to_date = _clean_text((period or {}).get("to_date"))
	if from_date and to_date:
		return f"for the period {from_date} to {to_date}"
	if to_date:
		return f"as of {to_date}"
	return ""


def _pluralize_label(label: str, count: int) -> str:
	text = _clean_text(label)
	if not text:
		return "Items" if count != 1 else "Item"
	if count == 1:
		return text
	lower = text.lower()
	if lower.endswith("ies") or lower.endswith("ses"):
		return text
	if lower.endswith("y") and len(text) > 1 and text[-2].lower() not in "aeiou":
		return text[:-1] + "ies"
	if lower.endswith("s"):
		return text
	return text + "s"


def _markdown_table(headers: List[str], rows: List[List[str]]) -> str:
	if not headers or not rows:
		return ""
	out = [
		"| " + " | ".join(headers) + " |",
		"| " + " | ".join("---" for _ in headers) + " |",
	]
	for row in rows:
		out.append("| " + " | ".join(str(cell or "") for cell in row) + " |")
	return "\n".join(out)


def _blocks_to_text(title: str, blocks: List[Dict[str, Any]]) -> str:
	lines: List[str] = [title]
	for block in blocks:
		if not isinstance(block, dict):
			continue
		block_title = _clean_text(block.get("title"))
		block_type = _clean_text(block.get("block_type"))
		if block_title:
			lines.append("")
			lines.append(block_title)
		if block_type == "summary_table":
			columns = [_clean_text(item) for item in block.get("columns") or [] if _clean_text(item)]
			rows = [
				[_clean_text(cell) for cell in row]
				for row in (block.get("rows") or [])
				if isinstance(row, list)
			]
			table = _markdown_table(columns, rows)
			if table:
				lines.append(table)
		elif block_type == "data_table":
			columns = [_clean_text(item) for item in block.get("columns") or [] if _clean_text(item)]
			rows = [
				[_clean_text(cell) for cell in row]
				for row in (block.get("rows") or [])
				if isinstance(row, list)
			]
			table = _markdown_table(columns, rows)
			if table:
				lines.append(table)
		elif block_type == "bullet_list":
			for item in block.get("items") or []:
				text = _clean_text(item)
				if text:
					lines.append(f"- {text}")
	return "\n".join(lines).strip()


def _statement_title(statement_type: str, source_reports: List[str]) -> str:
	source_report = _clean_text(source_reports[0] if source_reports else "")
	if source_report:
		return source_report
	return financial_statement_report_name(statement_type) or "Financial Statement"


def _projection_dimension_key(label: str) -> str:
	key = _clean_text(label).lower().replace(" ", "_")
	return {
		"customer": "entity",
		"supplier": "entity",
		"item": "entity",
		"product": "entity",
		"entity": "entity",
		"territory": "region",
		"country": "region",
		"brand": "region",
		"region": "region",
		"customer_group": "group",
		"supplier_group": "group",
		"item_group": "group",
		"group": "group",
		"creation": "creation",
		"created_date": "creation",
		"status": "status",
		"default_price_list": "default_price_list",
		"payment_terms": "payment_terms",
	}.get(key, "")


def _default_master_data_columns(
	*,
	scope_id: str,
	entity_type: str,
	lookup_projection: str,
	column_map: Dict[str, str],
) -> List[str]:
	if lookup_projection == "names_only":
		return ["entity"]
	if lookup_projection != "standard_directory":
		return ["entity"]
	resolved_scope_id = _clean_text(scope_id) or scope_id_for_entity_grain(entity_type)
	projection_spec = get_scope_projection_spec(resolved_scope_id, "master_data_lookup")
	allowed_dimensions = _clean_list(projection_spec.get("allowed_dimensions"))
	selected_columns: List[str] = []
	for dimension_label in allowed_dimensions:
		key = _projection_dimension_key(dimension_label)
		if key and key in column_map and key not in selected_columns:
			selected_columns.append(key)
	return selected_columns or ["entity"]


def _transaction_projection_key(
	label: str,
	*,
	column_map: Dict[str, str],
) -> str:
	normalized = _clean_text(label).lower()
	if not normalized:
		return ""
	for key, display_label in column_map.items():
		if normalized == _clean_text(display_label).lower():
			return key
	return {
		"customer": "party_name",
		"supplier": "party_name",
		"party": "party_name",
		"posting date": "posting_date",
		"transaction date": "posting_date",
		"delivery date": "delivery_date",
		"schedule date": "schedule_date",
		"document status": "status",
		"status": "status",
		"quantity": "quantity",
		"grand total": "grand_total",
		"outstanding amount": "outstanding_amount",
		"received amount": "received_amount",
		"total allocated amount": "total_allocated_amount",
		"paid amount": "paid_amount",
	}.get(normalized, "")


def _default_transaction_columns(
	*,
	scope_id: str,
	column_map: Dict[str, str],
	document_rows: List[Dict[str, Any]],
) -> List[str]:
	projection_spec = get_scope_projection_spec(_clean_text(scope_id), "transaction_listing")
	allowed_dimensions = _clean_list(projection_spec.get("allowed_dimensions"))
	allowed_metrics = _clean_list(projection_spec.get("allowed_metrics"))
	selected_columns: List[str] = []
	for label in allowed_dimensions + allowed_metrics:
		key = _transaction_projection_key(label, column_map=column_map)
		if not key or key not in column_map or key in selected_columns:
			continue
		if key in {"document_name", "posting_date", "party_name"}:
			selected_columns.append(key)
			continue
		if any(isinstance(row, dict) and key in row for row in document_rows):
			selected_columns.append(key)
	return selected_columns


def _top_section_rows(rows: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
	clean = [dict(item) for item in rows if isinstance(item, dict) and _clean_text(item.get("label"))]
	clean.sort(key=lambda item: abs(_float_value(item.get("amount"))), reverse=True)
	return clean[:limit]


_GENERIC_STATEMENT_LABELS = {
	"income",
	"direct income",
	"expenses",
	"direct expenses",
	"stock expenses",
	"assets",
	"liabilities",
	"equity",
}


def _statement_row_priority(item: Dict[str, Any]) -> tuple[int, int]:
	label = _clean_text(item.get("label")).lower()
	indent = int(_float_value(item.get("indent")))
	return (0 if label in _GENERIC_STATEMENT_LABELS else 1, indent, len(label))


def _top_statement_section_rows(rows: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
	grouped: Dict[str, Dict[str, Any]] = {}
	for item in rows:
		if not isinstance(item, dict) or not _clean_text(item.get("label")):
			continue
		key = f"{_float_value(item.get('amount')):.2f}"
		candidate = dict(item)
		existing = grouped.get(key)
		if existing is None or _statement_row_priority(candidate) > _statement_row_priority(existing):
			grouped[key] = candidate
	distinct = list(grouped.values())
	distinct.sort(key=lambda item: abs(_float_value(item.get("amount"))), reverse=True)
	return distinct[:limit]


def _statement_leaf_candidates(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	parent_accounts = {
		_clean_text(item.get("parent_account"))
		for item in rows
		if isinstance(item, dict) and _clean_text(item.get("parent_account"))
	}
	return [
		dict(item)
		for item in rows
		if isinstance(item, dict)
		and _clean_text(item.get("label"))
		and abs(_float_value(item.get("amount"))) > 0.0001
		and _clean_text(item.get("account")) not in parent_accounts
	]


def _project_statement_rows(rows: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
	all_rows = _top_statement_section_rows(rows, limit=max(limit * 3, 12))
	if not all_rows:
		return []
	leaf_rows = _statement_leaf_candidates(all_rows)
	non_generic_leaf_rows = [
		item
		for item in leaf_rows
		if _clean_text(item.get("label")).lower() not in _GENERIC_STATEMENT_LABELS
	]
	preferred_rows = [
		item
		for item in non_generic_leaf_rows
		if int(_float_value(item.get("indent"))) >= 2
	]
	if not preferred_rows:
		preferred_rows = [
			item
			for item in non_generic_leaf_rows
			if int(_float_value(item.get("indent"))) >= 1
		]
	if not preferred_rows:
		preferred_rows = non_generic_leaf_rows
	if not preferred_rows:
		preferred_rows = [
			item
			for item in all_rows
			if _clean_text(item.get("label")).lower() not in _GENERIC_STATEMENT_LABELS
			and abs(_float_value(item.get("amount"))) > 0.0001
		]
	if not preferred_rows:
		preferred_rows = [item for item in all_rows if abs(_float_value(item.get("amount"))) > 0.0001]
	return preferred_rows[:limit]


def _statement_line_phrase(item: Dict[str, Any], currency: str) -> str:
	label = _clean_text(item.get("label"))
	amount = _amount_text(item.get("amount"), _clean_text(item.get("currency") or currency))
	return f"{label} ({amount})".strip()


def _statement_section_bullet(section_label: str, rows: List[Dict[str, Any]], currency: str, limit: int = 3) -> str:
	top_rows = _project_statement_rows(rows, limit=limit)
	if not top_rows:
		return ""
	phrases = [_statement_line_phrase(item, currency) for item in top_rows if _clean_text(item.get("label"))]
	if not phrases:
		return ""
	return f"Key {section_label} lines: {', '.join(phrases)}."


def _financial_statement_notable_items(
	statement_type: str,
	sections: Dict[str, Any],
	currency: str,
) -> List[str]:
	if statement_type == "profit_and_loss":
		return [
			item
			for item in (
				_statement_section_bullet("income", _clean_rows(sections.get("income")), currency),
				_statement_section_bullet("expense", _clean_rows(sections.get("expense")), currency),
			)
			if item
		]
	if statement_type == "balance_sheet":
		return [
			item
			for item in (
				_statement_section_bullet("asset", _clean_rows(sections.get("assets")), currency),
				_statement_section_bullet("liability", _clean_rows(sections.get("liabilities")), currency),
				_statement_section_bullet("equity", _clean_rows(sections.get("equity")), currency, limit=2),
			)
			if item
		]
	return [
		item
		for item in (
			_statement_section_bullet("operating cash flow", _clean_rows(sections.get("operations")), currency),
			_statement_section_bullet("investing cash flow", _clean_rows(sections.get("investing")), currency, limit=2),
			_statement_section_bullet("financing cash flow", _clean_rows(sections.get("financing")), currency, limit=2),
		)
		if item
	]


def _financial_statement_summary_sentence(artifact: NormalizedFamilyArtifactContract) -> str:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	metrics = artifact.metrics if isinstance(artifact.metrics, dict) else {}
	currency = _clean_text(dimensions.get("currency"))
	statement_type = _clean_text(dimensions.get("statement_type"))
	company = _clean_text((artifact.filters if isinstance(artifact.filters, dict) else {}).get("company"))
	company_phrase = f" for {company}" if company else ""
	period_phrase = _period_phrase(artifact.period if isinstance(artifact.period, dict) else {})
	period_suffix = f" {period_phrase}" if period_phrase else ""
	if statement_type == "profit_and_loss":
		return (
			f"The Profit and Loss Statement{company_phrase}{period_suffix} shows total income of "
			f"{_amount_text(metrics.get('total_income'), currency)}, total expenses of "
			f"{_amount_text(metrics.get('total_expense'), currency)}, and net profit of "
			f"{_amount_text(metrics.get('net_profit'), currency)}."
		)
	if statement_type == "balance_sheet":
		sentence = (
			f"The Balance Sheet{company_phrase}{period_suffix} shows total assets of "
			f"{_amount_text(metrics.get('total_asset'), currency)}, total liabilities of "
			f"{_amount_text(metrics.get('total_liability'), currency)}, and total equity of "
			f"{_amount_text(metrics.get('total_equity'), currency)}"
		)
		provisional = _float_value(metrics.get("provisional_profit_or_loss"))
		if provisional:
			sentence += f", with provisional profit / loss of {_amount_text(provisional, currency)}"
		return sentence + "."
	return (
		f"The Cash Flow statement{company_phrase}{period_suffix} shows net cash from operations of "
		f"{_amount_text(metrics.get('net_cash_from_operations'), currency)}, net cash from investing of "
		f"{_amount_text(metrics.get('net_cash_from_investing'), currency)}, net cash from financing of "
		f"{_amount_text(metrics.get('net_cash_from_financing'), currency)}, and net change in cash of "
		f"{_amount_text(metrics.get('net_change_in_cash'), currency)}."
	)


def _financial_statement_answer_text(
	artifact: NormalizedFamilyArtifactContract,
	title: str,
	blocks: List[Dict[str, Any]],
) -> str:
	lines: List[str] = [title, "", _financial_statement_summary_sentence(artifact)]
	for block in blocks:
		if not isinstance(block, dict):
			continue
		block_title = _clean_text(block.get("title"))
		block_type = _clean_text(block.get("block_type"))
		if block_title:
			lines.append("")
			lines.append(block_title)
		if block_type in {"summary_table", "data_table"}:
			columns = [_clean_text(item) for item in block.get("columns") or [] if _clean_text(item)]
			rows = [
				[_clean_text(cell) for cell in row]
				for row in (block.get("rows") or [])
				if isinstance(row, list)
			]
			table = _markdown_table(columns, rows)
			if table:
				lines.append(table)
		elif block_type == "bullet_list":
			for item in block.get("items") or []:
				text = _clean_text(item)
				if text:
					lines.append(f"- {text}")
	return "\n".join(lines).strip()


def _financial_statement_blocks(artifact: NormalizedFamilyArtifactContract) -> tuple[str, List[Dict[str, Any]]]:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	metrics = artifact.metrics if isinstance(artifact.metrics, dict) else {}
	sections = artifact.sections if isinstance(artifact.sections, dict) else {}
	statement_type = _clean_text(dimensions.get("statement_type"))
	currency = _clean_text(dimensions.get("currency"))
	title = _title_with_period(_statement_title(statement_type, artifact.source_reports), artifact.period)

	summary_rows: List[List[str]] = []
	section_blocks: List[Dict[str, Any]] = []
	if statement_type == "profit_and_loss":
		summary_rows = [
			["Total Income", _amount_text(metrics.get("total_income"), currency)],
			["Total Expense", _amount_text(metrics.get("total_expense"), currency)],
			["Net Profit", _amount_text(metrics.get("net_profit"), currency)],
		]
		for section_name, label in (("income", "Top Income Lines"), ("expense", "Top Expense Lines")):
			top_rows = _project_statement_rows(_clean_rows(sections.get(section_name)))
			if not top_rows:
				continue
			section_blocks.append(
				{
					"block_type": "data_table",
					"title": label,
					"columns": ["Account", "Amount"],
					"rows": [[_clean_text(item.get("label")), _amount_text(item.get("amount"), _clean_text(item.get("currency") or currency))] for item in top_rows],
				}
			)
	elif statement_type == "balance_sheet":
		summary_rows = [
			["Total Assets", _amount_text(metrics.get("total_asset"), currency)],
			["Total Liabilities", _amount_text(metrics.get("total_liability"), currency)],
			["Total Equity", _amount_text(metrics.get("total_equity"), currency)],
		]
		provisional = _float_value(metrics.get("provisional_profit_or_loss"))
		if provisional:
			summary_rows.append(["Provisional Profit / Loss", _amount_text(provisional, currency)])
		for section_name, label in (("assets", "Top Asset Lines"), ("liabilities", "Top Liability Lines"), ("equity", "Top Equity Lines")):
			top_rows = _project_statement_rows(_clean_rows(sections.get(section_name)))
			if not top_rows:
				continue
			section_blocks.append(
				{
					"block_type": "data_table",
					"title": label,
					"columns": ["Account", "Amount"],
					"rows": [[_clean_text(item.get("label")), _amount_text(item.get("amount"), _clean_text(item.get("currency") or currency))] for item in top_rows],
				}
			)
	else:
		summary_rows = [
			["Net Cash from Operations", _amount_text(metrics.get("net_cash_from_operations"), currency)],
			["Net Cash from Investing", _amount_text(metrics.get("net_cash_from_investing"), currency)],
			["Net Cash from Financing", _amount_text(metrics.get("net_cash_from_financing"), currency)],
			["Net Change in Cash", _amount_text(metrics.get("net_change_in_cash"), currency)],
		]
		for section_name, label in (("operations", "Operating Cash Flows"), ("investing", "Investing Cash Flows"), ("financing", "Financing Cash Flows")):
			top_rows = _project_statement_rows(_clean_rows(sections.get(section_name)))
			if not top_rows:
				continue
			section_blocks.append(
				{
					"block_type": "data_table",
					"title": label,
					"columns": ["Line", "Amount"],
					"rows": [[_clean_text(item.get("label")), _amount_text(item.get("amount"), _clean_text(item.get("currency") or currency))] for item in top_rows],
				}
			)

	blocks: List[Dict[str, Any]] = [
		{
			"block_type": "summary_table",
			"title": "Summary",
			"columns": ["Metric", "Amount"],
			"rows": summary_rows,
		}
	]
	notable_items = _financial_statement_notable_items(statement_type, sections, currency)
	if notable_items:
		blocks.append(
			{
				"block_type": "bullet_list",
				"title": "Notable Line Items",
				"items": notable_items,
			}
		)
	blocks.extend(section_blocks)
	return title, blocks


def _aging_title(artifact: NormalizedFamilyArtifactContract) -> str:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	aging_type = _clean_text(dimensions.get("aging_type"))
	title = "Accounts Aging"
	if aging_type == "accounts_receivable":
		title = "Accounts Receivable Aging"
	elif aging_type == "accounts_payable":
		title = "Accounts Payable Aging"
	return _title_with_period(title, artifact.period)


def _aging_overdue_31_plus(item: Dict[str, Any]) -> float:
	return sum(
		_float_value(item.get(key))
		for key in ("bucket_31_60", "bucket_61_90", "bucket_91_120", "bucket_121_above")
	)


def _aging_blocks(artifact: NormalizedFamilyArtifactContract) -> tuple[str, List[Dict[str, Any]]]:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	sections = artifact.sections if isinstance(artifact.sections, dict) else {}
	currency = _clean_text(dimensions.get("currency"))
	party_label = _clean_text(dimensions.get("party_dimension_label")) or "Party"
	parties = _clean_rows(sections.get("parties"))
	parties.sort(key=lambda item: _float_value(item.get("outstanding")), reverse=True)
	bucket_totals = _clean_rows(sections.get("bucket_totals"))
	summary = _clean_rows(sections.get("summary"))
	title = _aging_title(artifact)
	blocks = [
		{
			"block_type": "summary_table",
			"title": "Summary",
			"columns": ["Metric", "Value"],
			"rows": [
				[
					_clean_text(item.get("label")),
					_ratio_text(item.get("value")) if _clean_text(item.get("metric_key")) == "overdue_ratio" else _amount_text(item.get("amount"), _clean_text(item.get("currency") or currency)),
				]
				for item in summary
			],
		},
		{
			"block_type": "data_table",
			"title": "Bucket Totals",
			"columns": ["Bucket", "Amount"],
			"rows": [[_clean_text(item.get("label")), _amount_text(item.get("amount"), _clean_text(item.get("currency") or currency))] for item in bucket_totals],
		},
	]
	top_parties = parties[:10]
	if top_parties:
		blocks.append(
			{
				"block_type": "data_table",
				"title": f"Top {party_label}s",
				"columns": [party_label, "Outstanding", "Total Due", "Overdue (31+)"],
				"rows": [
					[
						_clean_text(item.get("party")),
						_amount_text(item.get("outstanding"), _clean_text(item.get("currency") or currency)),
						_amount_text(item.get("total_due"), _clean_text(item.get("currency") or currency)),
						_amount_text(_aging_overdue_31_plus(item), _clean_text(item.get("currency") or currency)),
					]
					for item in top_parties
				],
			}
		)
	return title, blocks


def _ranking_blocks(
	artifact: NormalizedFamilyArtifactContract,
	response_overrides: Dict[str, Any] | None = None,
) -> tuple[str, List[Dict[str, Any]]]:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	sections = artifact.sections if isinstance(artifact.sections, dict) else {}
	entity_label = _clean_text(dimensions.get("entity_dimension")) or "Entity"
	all_ranked_rows = _clean_rows(sections.get("ranked_rows"))
	metric_key = _preferred_metric_key(all_ranked_rows, dimensions, response_overrides)
	metric_label = _metric_label(metric_key, _clean_text(dimensions.get("primary_metric_label")) or "Primary Metric")
	top_n = _requested_top_n(dimensions, response_overrides, default=10)
	sort_direction = _requested_sort_direction(dimensions, response_overrides, default="desc")
	if sort_direction == "asc":
		ranked_rows = list(reversed(all_ranked_rows))[:top_n]
		display_count = _display_row_count(top_n, ranked_rows)
		title = _title_with_period(f"Bottom {display_count} {entity_label}s by {metric_label}", artifact.period)
		table_title = "Bottom Ranked Rows"
	else:
		ranked_rows = all_ranked_rows[:top_n]
		display_count = _display_row_count(top_n, ranked_rows)
		title = _title_with_period(f"Top {display_count} {entity_label}s by {metric_label}", artifact.period)
		table_title = "Top Ranked Rows"
	summary = _clean_rows(sections.get("summary"))
	requested_columns = _normalized_metric_projection_columns(
		_requested_columns(dimensions, response_overrides),
		metric_key,
	)
	# Extract show_million from response_overrides
	show_million = bool((response_overrides or {}).get("show_million"))
	table_headers, table_rows = _ranking_table_spec(
		rows=ranked_rows,
		entity_label=entity_label,
		metric_key=metric_key,
		metric_label=metric_label,
		requested_columns=requested_columns,
		show_million=show_million,
	)
	blocks: List[Dict[str, Any]] = []
	if summary and not _suppress_summary_block(dimensions, response_overrides):
		blocks.append(
			{
				"block_type": "summary_table",
				"title": "Summary",
				"columns": ["Metric", "Value"],
				"rows": [
					[
						_clean_text(item.get("label")),
						_amount_text(item.get("amount"), show_million=show_million) if item.get("amount") not in (None, "") else _clean_text(item.get("value")),
					]
					for item in summary
				],
			}
		)
	if ranked_rows:
		blocks.append(
			{
				"block_type": "data_table",
				"title": table_title,
				"columns": table_headers,
				"rows": table_rows,
			}
		)
	return title, blocks


def _trend_blocks(artifact: NormalizedFamilyArtifactContract) -> tuple[str, List[Dict[str, Any]]]:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	sections = artifact.sections if isinstance(artifact.sections, dict) else {}
	metric_label = _clean_text(dimensions.get("primary_metric_label")) or "Value"
	time_grain = _clean_text(dimensions.get("time_grain")) or "periodic"
	title = _title_with_period(f"{metric_label} Trend ({time_grain.title()})", artifact.period)
	series = _clean_rows(sections.get("period_series"))
	total_value = sum(_float_value(item.get("value")) for item in series)
	peak = max(series, key=lambda item: _float_value(item.get("value")), default={})
	low = min(series, key=lambda item: _float_value(item.get("value")), default={})
	blocks = [
		{
			"block_type": "summary_table",
			"title": "Summary",
			"columns": ["Metric", "Value"],
			"rows": [
				["Total " + metric_label, _amount_text(total_value)],
				["Period Count", str(len(series))],
				["Peak Period", _clean_text(peak.get("label")) or "-"],
				["Peak Value", _amount_text(peak.get("value"))],
				["Lowest Period", _clean_text(low.get("label")) or "-"],
				["Lowest Value", _amount_text(low.get("value"))],
			],
		}
	]
	if series:
		blocks.append(
			{
				"block_type": "data_table",
				"title": "Period Series",
				"columns": ["Period", metric_label],
				"rows": [[_clean_text(item.get("label") or item.get("period_key")), _amount_text(item.get("value"))] for item in series],
			}
		)
	return title, blocks


def _inventory_blocks(
	artifact: NormalizedFamilyArtifactContract,
	response_overrides: Dict[str, Any] | None = None,
) -> tuple[str, List[Dict[str, Any]]]:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	sections = artifact.sections if isinstance(artifact.sections, dict) else {}
	title = _title_with_period("Inventory Snapshot", artifact.period)
	summary = _clean_rows(sections.get("summary"))
	snapshot_dimension = _clean_text(dimensions.get("snapshot_dimension")) or "Item"
	snapshot_label = snapshot_dimension.replace("_", " ").title() or "Item"
	if snapshot_dimension.lower() == "warehouse":
		all_rows = _clean_rows(sections.get("warehouse_totals"))
		entity_key = "warehouse"
	else:
		all_rows = _clean_rows(sections.get("item_totals"))
		entity_key = "item"
	top_n = _requested_top_n(dimensions, response_overrides, default=10)
	sort_direction = _requested_sort_direction(dimensions, response_overrides, default="desc")
	rows = list(reversed(all_rows))[:top_n] if sort_direction == "asc" else all_rows[:top_n]
	blocks: List[Dict[str, Any]] = []
	if summary and not _suppress_summary_block(dimensions, response_overrides):
		blocks.append(
			{
				"block_type": "summary_table",
				"title": "Summary",
				"columns": ["Metric", "Value"],
				"rows": [
					[
						_clean_text(item.get("label")),
						_amount_text(item.get("amount")) if item.get("amount") not in (None, "") else _clean_text(item.get("value")),
					]
					for item in summary
				],
			}
		)
	if rows:
		blocks.append(
			{
				"block_type": "data_table",
				"title": f"Top {snapshot_label}s",
				"columns": [snapshot_label, "Balance Qty", "Balance Value"],
				"rows": [
					[
						_clean_text(item.get(entity_key)),
						_amount_text(item.get("balance_qty")),
						_amount_text(item.get("balance_value")),
					]
					for item in rows
				],
			}
		)
	return title, blocks


def _product_blocks(
	artifact: NormalizedFamilyArtifactContract,
	response_overrides: Dict[str, Any] | None = None,
) -> tuple[str, List[Dict[str, Any]]]:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	sections = artifact.sections if isinstance(artifact.sections, dict) else {}
	product_rows_all = _clean_rows(sections.get("product_rows"))
	metric_key = _preferred_metric_key(product_rows_all, dimensions, response_overrides)
	metric_label = _metric_label(metric_key, _clean_text(dimensions.get("primary_metric_label")) or "Primary Metric")
	top_n = _requested_top_n(dimensions, response_overrides, default=10)
	sort_direction = _requested_sort_direction(dimensions, response_overrides, default="desc")
	if sort_direction == "asc":
		product_rows = list(reversed(product_rows_all))[:top_n]
		display_count = _display_row_count(top_n, product_rows)
		title = _title_with_period(f"Bottom {display_count} Products by {metric_label}", artifact.period)
		table_title = "Bottom Products"
	else:
		product_rows = product_rows_all[:top_n]
		display_count = _display_row_count(top_n, product_rows)
		title = _title_with_period(f"Top {display_count} Products by {metric_label}", artifact.period)
		table_title = "Top Products"
	summary = _clean_rows(sections.get("summary"))
	requested_columns = _normalized_metric_projection_columns(
		_requested_columns(dimensions, response_overrides),
		metric_key,
	)
	blocks: List[Dict[str, Any]] = []
	if summary and not _suppress_summary_block(dimensions, response_overrides):
		blocks.append(
			{
				"block_type": "summary_table",
				"title": "Summary",
				"columns": ["Metric", "Value"],
				"rows": [
					[
						_clean_text(item.get("label")),
						_amount_text(item.get("amount")) if item.get("amount") not in (None, "") else _clean_text(item.get("value")),
					]
					for item in summary
				],
			}
		)
	if product_rows:
		if requested_columns:
			table_headers, table_rows = _ranking_table_spec(
				rows=product_rows,
				entity_label="Product",
				metric_key=metric_key,
				metric_label=metric_label,
				requested_columns=requested_columns,
			)
		else:
			table_headers = ["Product", metric_label, "Sales Amount", "Gross Profit %"]
			table_rows = [
				[
					_clean_text(item.get("item_name") or item.get("item") or item.get("item_code")),
					_ratio_text(item.get(metric_key)) if metric_key == "gross_profit_percent" else _amount_text(item.get(metric_key)),
					_amount_text(item.get("sales_amount")),
					_ratio_text(item.get("gross_profit_percent")) if item.get("gross_profit_percent") not in (None, "") else "",
				]
				for item in product_rows
			]
		blocks.append(
			{
				"block_type": "data_table",
				"title": table_title,
				"columns": table_headers,
				"rows": table_rows,
			}
		)
	return title, blocks


def _transaction_listing_blocks(artifact: NormalizedFamilyArtifactContract) -> tuple[str, List[Dict[str, Any]]]:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	sections = artifact.sections if isinstance(artifact.sections, dict) else {}
	document_rows = _clean_rows(sections.get("transaction_rows"))
	summary = _clean_rows(sections.get("summary"))
	top_n = _requested_top_n(dimensions, None, default=len(document_rows) or 10)
	document_label = _clean_text(dimensions.get("document_label")) or "Transactions"
	sort_direction = _requested_sort_direction(dimensions, None, default="desc")
	title_prefix = "First" if sort_direction == "asc" else "Last"
	limited_count = _display_row_count(top_n, (list(reversed(document_rows)) if sort_direction == "asc" else list(document_rows))[:top_n])
	title = _title_with_period(f"{title_prefix} {limited_count} {_pluralize_label(document_label, limited_count)}", artifact.period)
	requested_columns = _requested_columns(dimensions, None)
	party_field = _clean_text(dimensions.get("party_field")) or ("customer" if any(_clean_text(row.get("customer")) for row in document_rows) else "party_name")
	party_label = _clean_text(dimensions.get("party_label")) or "Party"
	date_label = _clean_text(dimensions.get("date_label")) or "Posting Date"
	scope_id = _clean_text(dimensions.get("scope_id")) or _clean_text(dimensions.get("transaction_type"))
	primary_metric_key = _clean_text(dimensions.get("primary_metric_key")) or "grand_total"
	primary_metric_label = _clean_text(dimensions.get("primary_metric_label")) or "Grand Total"
	metric_label_map = (
		dict(dimensions.get("metric_label_map"))
		if isinstance(dimensions.get("metric_label_map"), dict)
		else {}
	)
	if metric_label_map:
		metric_label_map = {
			_clean_text(key).lower().replace(" ", "_"): _clean_text(value)
			for key, value in metric_label_map.items()
			if _clean_text(key) and _clean_text(value)
		}
	has_party_column = any(_clean_text(row.get(party_field) or row.get("party_name")) for row in document_rows)
	column_map = {
		"document_name": document_label,
		"posting_date": date_label,
		"delivery_date": "Delivery Date",
		"schedule_date": "Schedule Date",
		"customer": party_label,
		"supplier": party_label,
		"party_name": party_label,
		primary_metric_key: primary_metric_label,
		"grand_total": "Grand Total",
		"received_amount": _clean_text(metric_label_map.get("received_amount")) or "Received Amount",
		"total_allocated_amount": _clean_text(metric_label_map.get("total_allocated_amount")) or "Total Allocated Amount",
		"paid_amount": _clean_text(metric_label_map.get("paid_amount")) or "Paid Amount",
		"quantity": "Quantity",
		"outstanding_amount": "Outstanding Amount",
		"status": "Status",
	}
	default_columns = _default_transaction_columns(
		scope_id=scope_id,
		column_map=column_map,
		document_rows=document_rows,
	)
	has_explicit_projection_request = bool(dimensions.get("has_explicit_projection_request"))
	available_columns = ["document_name", "posting_date"]
	if has_party_column:
		available_columns.append("party_name")
	if any(_clean_text(row.get("delivery_date")) for row in document_rows):
		available_columns.append("delivery_date")
	if any(_clean_text(row.get("schedule_date")) for row in document_rows):
		available_columns.append("schedule_date")
	if any(row.get(quantity_key) not in (None, "", 0) for quantity_key in ["quantity"] for row in document_rows):
		available_columns.append("quantity")
	if any(row.get(primary_metric_key) not in (None, "", 0) for row in document_rows):
		available_columns.append(primary_metric_key)
	if any(row.get("outstanding_amount") not in (None, "", 0) for row in document_rows):
		available_columns.append("outstanding_amount")
	available_columns.append("status")
	selected_columns = (
		requested_columns
		if has_explicit_projection_request and requested_columns
		else default_columns or requested_columns or available_columns
	)
	selected_columns = [value for value in selected_columns if value in column_map]
	base_columns = [value for value in default_columns if value in {"document_name", "posting_date", "party_name"}]
	if not base_columns:
		base_columns = ["document_name", "posting_date"]
		if has_party_column:
			base_columns.append("party_name")
	for key in reversed(base_columns):
		if key not in selected_columns:
			selected_columns.insert(0, key)
	blocks = [
		{
			"block_type": "summary_table",
			"title": "Summary",
			"columns": ["Metric", "Value"],
			"rows": [
				[
					_clean_text(item.get("label")),
					_amount_text(item.get("amount")) if item.get("amount") not in (None, "") else _clean_text(item.get("value")),
				]
				for item in summary
			],
		}
	]
	if document_rows:
		ordered_rows = list(reversed(document_rows)) if sort_direction == "asc" else list(document_rows)
		limited_rows = ordered_rows[:top_n]
		table_rows: List[List[str]] = []
		for row in limited_rows:
			out: List[str] = []
			for key in selected_columns:
				if key in {"posting_date", "delivery_date", "schedule_date"}:
					out.append(_clean_text(row.get(key)))
				elif key == "status":
					out.append(_clean_text(row.get(key)))
				elif key in {"customer", "party_name"}:
					out.append(_clean_text(row.get(key) or row.get("party_name") or row.get("customer")))
				elif key == "document_name":
					out.append(_clean_text(row.get(key)))
				else:
					metric_values = dict(row.get("metric_values")) if isinstance(row.get("metric_values"), dict) else {}
					out.append(_amount_text(row.get(key) if row.get(key) not in (None, "") else metric_values.get(key)))
			table_rows.append(out)
		blocks.append(
			{
				"block_type": "data_table",
				"title": "Documents",
				"columns": [column_map[key] for key in selected_columns],
				"rows": table_rows,
			}
		)
	else:
		blocks.append(
			{
				"block_type": "bullet_list",
				"title": "Result",
				"items": ["No documents matched these filters."],
			}
		)
	return title, blocks


def _master_data_directory_blocks(artifact: NormalizedFamilyArtifactContract) -> tuple[str, List[Dict[str, Any]]]:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	sections = artifact.sections if isinstance(artifact.sections, dict) else {}
	directory_rows = _clean_rows(sections.get("directory_rows") or sections.get("customer_rows"))
	lookup_mode = _clean_text(dimensions.get("lookup_mode"))
	lookup_projection = _clean_text(dimensions.get("lookup_projection"))
	lookup_search_text = _clean_text(dimensions.get("lookup_search_text"))
	scope_id = _clean_text(dimensions.get("scope_id"))
	entity_type = _clean_text(dimensions.get("entity_type")) or "customer"
	entity_label = _clean_text(dimensions.get("entity_label")) or entity_type.title()
	entity_plural_label = _clean_text(dimensions.get("entity_plural_label")) or f"{entity_label}s"
	group_label = _clean_text(dimensions.get("group_label")) or "Group"
	region_label = _clean_text(dimensions.get("region_label")) or "Region"
	entity_reference_resolution = (
		dict(sections.get("entity_reference_resolution"))
		if isinstance(sections.get("entity_reference_resolution"), dict)
		else {}
	)
	top_n = _requested_top_n(dimensions, None, default=len(directory_rows) or 10)
	title = _title_with_period(entity_plural_label, artifact.period)
	requested_columns = _requested_columns(dimensions, None)
	column_map = {
		"entity": entity_label,
		"region": region_label,
		"group": group_label,
		"creation": "Created Date",
		"status": "Status",
		"default_price_list": "Default Price List",
		"payment_terms": "Payment Terms",
	}
	if requested_columns:
		selected_columns = [value for value in requested_columns if value in column_map] or ["entity"]
	else:
		selected_columns = _default_master_data_columns(
			scope_id=scope_id,
			entity_type=entity_type,
			lookup_projection=lookup_projection,
			column_map=column_map,
		)
	limited_rows = directory_rows[:top_n]
	match_title = f"{entity_label} Match"
	if lookup_mode == "candidate_resolution" and entity_reference_resolution:
		resolution_status = _clean_text(entity_reference_resolution.get("resolution_status"))
		resolved_entity = (
			dict(entity_reference_resolution.get("resolved_entity"))
			if isinstance(entity_reference_resolution.get("resolved_entity"), dict)
			else {}
		)
		candidate_entities = _clean_rows(entity_reference_resolution.get("candidate_entities"))
		candidate_labels = list(
			dict.fromkeys(
				_clean_text(item.get("entity_label") or item.get("entity_key"))
				for item in candidate_entities
				if _clean_text(item.get("entity_label") or item.get("entity_key"))
			)
		)
		search_phrase = f' "{lookup_search_text}"' if lookup_search_text else ""
		if resolution_status == "resolved" and _clean_text(resolved_entity.get("entity_label") or resolved_entity.get("entity_key")):
			resolved_label = _clean_text(resolved_entity.get("entity_label") or resolved_entity.get("entity_key"))
			if selected_columns == ["entity"] or not limited_rows:
				return match_title, [
					{
						"block_type": "bullet_list",
						"title": "Result",
						"items": [f'The closest {entity_type} match for{search_phrase} is {resolved_label}.'],
					}
				]
			filtered_rows = [
				row
				for row in limited_rows
				if _clean_text(row.get("entity_code")) == _clean_text(resolved_entity.get("entity_key"))
			] or limited_rows[:1]
			table_rows: List[List[str]] = []
			for row in filtered_rows:
				out: List[str] = []
				for key in selected_columns:
					if key == "entity":
						out.append(_clean_text(row.get("entity") or row.get("entity_name")))
					elif key == "status":
						out.append(_clean_text(row.get("status") or row.get("document_status")))
					else:
						out.append(_clean_text(row.get(key)))
				table_rows.append(out)
			return match_title, [
				{
					"block_type": "bullet_list",
					"title": "Result",
					"items": [f'The closest {entity_type} match for{search_phrase} is {resolved_label}.'],
				},
				{
					"block_type": "data_table",
					"title": f"Matched {entity_label}",
					"columns": [column_map[key] for key in selected_columns],
					"rows": table_rows,
				},
			]
		if resolution_status == "ambiguous" and candidate_labels:
			return f"Possible {entity_plural_label}", [
				{
					"block_type": "bullet_list",
					"title": f"{entity_label} Names",
					"items": candidate_labels,
				}
			]
		if resolution_status == "not_found":
			items = [f'No {entity_type} match was found for{search_phrase}.']
			suggested_candidates = candidate_labels
			if suggested_candidates:
				items.append("Closest names: " + ", ".join(suggested_candidates[:5]) + ".")
			return match_title, [
				{
					"block_type": "bullet_list",
					"title": "Result",
					"items": items,
				}
			]
	if not limited_rows:
		return title, [
			{
				"block_type": "bullet_list",
				"title": "Result",
				"items": [f"No {entity_plural_label.lower()} matched these filters."],
			}
		]
	if selected_columns == ["entity"]:
		return title, [
			{
				"block_type": "bullet_list",
				"title": f"{entity_label} Names",
				"items": [_clean_text(row.get("entity") or row.get("entity_name")) for row in limited_rows],
			}
		]
	table_rows: List[List[str]] = []
	for row in limited_rows:
		out: List[str] = []
		for key in selected_columns:
			if key == "entity":
				out.append(_clean_text(row.get("entity") or row.get("entity_name")))
			elif key == "status":
				out.append(_clean_text(row.get("status") or row.get("document_status")))
			else:
				out.append(_clean_text(row.get(key)))
		table_rows.append(out)
	return title, [
		{
			"block_type": "data_table",
			"title": f"{entity_label} Rows",
			"columns": [column_map[key] for key in selected_columns],
			"rows": table_rows,
		}
	]


def _composite_working_capital_blocks(composite_artifact: Dict[str, Any]) -> tuple[str, List[Dict[str, Any]]]:
	period = composite_artifact.get("period") if isinstance(composite_artifact.get("period"), dict) else {}
	dimensions = composite_artifact.get("dimensions") if isinstance(composite_artifact.get("dimensions"), dict) else {}
	metrics = composite_artifact.get("metrics") if isinstance(composite_artifact.get("metrics"), dict) else {}
	summary_items = composite_artifact.get("sections") if isinstance(composite_artifact.get("sections"), dict) else {}
	currency = _clean_text(dimensions.get("currency")) or "MMK"
	title = _title_with_period("AR/AP Working Capital Health", period)
	blocks = [
		{
			"block_type": "summary_table",
			"title": "Summary",
			"columns": ["Metric", "Value"],
			"rows": [
				["Accounts Receivable Outstanding", _amount_text(metrics.get("accounts_receivable_outstanding_total"), currency)],
				["Accounts Payable Outstanding", _amount_text(metrics.get("accounts_payable_outstanding_total"), currency)],
				["Net AR minus AP", _amount_text(metrics.get("net_receivable_minus_payable"), currency)],
				["AR Overdue Ratio", _ratio_text(metrics.get("accounts_receivable_overdue_ratio"))],
				["AP Overdue Ratio", _ratio_text(metrics.get("accounts_payable_overdue_ratio"))],
			],
		}
	]
	observations = summary_items.get("summary") if isinstance(summary_items.get("summary"), list) else []
	if observations:
		blocks.append(
			{
				"block_type": "bullet_list",
				"title": "Key Observations",
				"items": [_clean_text(item) for item in observations if _clean_text(item)],
			}
		)
	return title, blocks


@dataclass(frozen=True)
class FamilyRenderOutcome:
	status: str
	contract: RenderedFamilyResponseContract | None = None
	errors: List[str] = field(default_factory=list)
	warnings: List[str] = field(default_factory=list)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_family_render_outcome",
			"contract_version": "1.0",
			"status": self.status,
			"errors": list(self.errors),
			"warnings": list(self.warnings),
			"contract": self.contract.to_payload() if self.contract else {},
		}


def render_normalized_family_response(
	*,
	request_id: str,
	artifact_contract: NormalizedFamilyArtifactContract | None,
	response_overrides: Dict[str, Any] | None = None,
) -> FamilyRenderOutcome:
	if artifact_contract is None:
		return FamilyRenderOutcome(
			status="render_not_available",
			errors=["Family rendering requires a normalized family artifact."],
		)
	family_id = _clean_text(artifact_contract.family_id)
	renderer_id = report_family_renderer_id(family_id) or f"{family_id}_renderer"
	title = ""
	blocks: List[Dict[str, Any]] = []
	if family_id == "financial_statement":
		title, blocks = _financial_statement_blocks(artifact_contract)
	elif family_id == "aging":
		title, blocks = _aging_blocks(artifact_contract)
	elif family_id == "ranking_analytics":
		title, blocks = _ranking_blocks(artifact_contract, response_overrides=response_overrides)
	elif family_id == "trend_analytics":
		title, blocks = _trend_blocks(artifact_contract)
	elif family_id == "inventory_snapshot":
		title, blocks = _inventory_blocks(artifact_contract, response_overrides=response_overrides)
	elif family_id == "product_profitability":
		title, blocks = _product_blocks(artifact_contract, response_overrides=response_overrides)
	elif family_id == "transaction_listing":
		title, blocks = _transaction_listing_blocks(artifact_contract)
	elif family_id in {"customer_master_list", "master_data_directory"}:
		title, blocks = _master_data_directory_blocks(artifact_contract)
	else:
		return FamilyRenderOutcome(
			status="render_not_available",
			errors=[f"No governed family renderer is defined for `{family_id}`."],
		)
	if family_id == "financial_statement":
		answer_text = _financial_statement_answer_text(artifact_contract, title, blocks)
	else:
		answer_text = _blocks_to_text(title, blocks)
	contract = build_rendered_family_response_contract(
		request_id=request_id,
		family_id=family_id,
		renderer_id=renderer_id,
		title=title,
		answer_text=answer_text,
		source_reports=list(artifact_contract.source_reports),
		blocks=blocks,
		warnings=list(artifact_contract.warnings),
	)
	return FamilyRenderOutcome(status="rendered", contract=contract, warnings=list(artifact_contract.warnings))


def render_composite_family_response(
	*,
	request_id: str,
	plan_id: str,
	composite_artifact: Dict[str, Any],
	source_reports: List[str],
	warnings: List[str] | None = None,
) -> FamilyRenderOutcome:
	if not isinstance(composite_artifact, dict) or not composite_artifact:
		return FamilyRenderOutcome(
			status="render_not_available",
			errors=["Composite rendering requires a normalized composite artifact."],
		)
	renderer_id = composite_read_renderer_id(plan_id) or f"{plan_id}_renderer"
	family_id = _clean_text(composite_artifact.get("family_id")) or f"composite::{plan_id}"
	title = ""
	blocks: List[Dict[str, Any]] = []
	if plan_id == "working_capital_health":
		title, blocks = _composite_working_capital_blocks(composite_artifact)
	else:
		return FamilyRenderOutcome(
			status="render_not_available",
			errors=[f"No governed composite renderer is defined for `{plan_id}`."],
		)
	answer_text = _blocks_to_text(title, blocks)
	contract = build_rendered_family_response_contract(
		request_id=request_id,
		family_id=family_id,
		renderer_id=renderer_id,
		title=title,
		answer_text=answer_text,
		source_reports=list(source_reports),
		blocks=blocks,
		warnings=list(warnings or []),
	)
	return FamilyRenderOutcome(status="rendered", contract=contract, warnings=list(warnings or []))
