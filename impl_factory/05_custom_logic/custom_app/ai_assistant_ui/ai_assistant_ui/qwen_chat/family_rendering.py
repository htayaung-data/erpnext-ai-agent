from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	NormalizedFamilyArtifactContract,
	RenderedFamilyResponseContract,
	build_rendered_family_response_contract,
)
from ai_assistant_ui.qwen_chat.metadata import composite_read_renderer_id, report_family_renderer_id


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
	return {
		"sales_amount": "Sales Amount",
		"gross_profit": "Gross Profit",
		"gross_profit_percent": "Gross Profit %",
		"buying_amount": "Buying Amount",
		"quantity": "Quantity",
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
	normalized: List[str] = []
	for value in values:
		key = _clean_text(value).lower().replace(" ", "_")
		if key in {"transaction_date", "posting_date"}:
			normalized.append("posting_date")
		elif key in {"customer", "supplier", "party", "party_name"}:
			normalized.append("party_name")
		elif key in {"status", "document_status"}:
			normalized.append("status")
		else:
			normalized.append(value)
	return list(dict.fromkeys([value for value in normalized if _clean_text(value)]))


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
	return {
		"profit_and_loss": "Profit and Loss Statement",
		"balance_sheet": "Balance Sheet",
		"cash_flow": "Cash Flow",
	}.get(statement_type, "Financial Statement")


def _top_section_rows(rows: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
	clean = [dict(item) for item in rows if isinstance(item, dict) and _clean_text(item.get("label"))]
	clean.sort(key=lambda item: abs(_float_value(item.get("amount"))), reverse=True)
	return clean[:limit]


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
			top_rows = _top_section_rows(_clean_rows(sections.get(section_name)))
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
			top_rows = _top_section_rows(_clean_rows(sections.get(section_name)))
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
			top_rows = _top_section_rows(_clean_rows(sections.get(section_name)))
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
		title = _title_with_period(f"Bottom {top_n} {entity_label}s by {metric_label}", artifact.period)
		table_title = "Bottom Ranked Rows"
	else:
		ranked_rows = all_ranked_rows[:top_n]
		title = _title_with_period(f"Top {top_n} {entity_label}s by {metric_label}", artifact.period)
		table_title = "Top Ranked Rows"
	summary = _clean_rows(sections.get("summary"))
	requested_columns = _requested_columns(dimensions, response_overrides)
	requested_columns = [metric_key if value == "amount" else value for value in requested_columns]
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
	blocks = [
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
		},
	]
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


def _inventory_blocks(artifact: NormalizedFamilyArtifactContract) -> tuple[str, List[Dict[str, Any]]]:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	sections = artifact.sections if isinstance(artifact.sections, dict) else {}
	title = _title_with_period("Inventory Snapshot", artifact.period)
	summary = _clean_rows(sections.get("summary"))
	snapshot_dimension = _clean_text(dimensions.get("snapshot_dimension")) or "Item"
	if snapshot_dimension.lower() == "warehouse":
		rows = _clean_rows(sections.get("warehouse_totals"))
		entity_key = "warehouse"
	else:
		rows = _clean_rows(sections.get("item_totals"))
		entity_key = "item"
	rows = rows[:10]
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
	if rows:
		blocks.append(
			{
				"block_type": "data_table",
				"title": f"Top {snapshot_dimension}s",
				"columns": [snapshot_dimension, "Balance Qty", "Balance Value"],
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
		title = _title_with_period(f"Bottom {top_n} Products by {metric_label}", artifact.period)
		product_rows = list(reversed(product_rows_all))[:top_n]
		table_title = "Bottom Products"
	else:
		title = _title_with_period(f"Top {top_n} Products by {metric_label}", artifact.period)
		product_rows = product_rows_all[:top_n]
		table_title = "Top Products"
	summary = _clean_rows(sections.get("summary"))
	requested_columns = _requested_columns(dimensions, response_overrides)
	requested_columns = [metric_key if value == "amount" else value for value in requested_columns]
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
	title = _title_with_period(f"Last {top_n} {document_label}s", artifact.period)
	requested_columns = _requested_columns(dimensions, None)
	party_field = _clean_text(dimensions.get("party_field")) or ("customer" if any(_clean_text(row.get("customer")) for row in document_rows) else "party_name")
	party_label = _clean_text(dimensions.get("party_label")) or "Party"
	date_label = _clean_text(dimensions.get("date_label")) or "Posting Date"
	has_party_column = any(_clean_text(row.get(party_field) or row.get("party_name")) for row in document_rows)
	column_map = {
		"document_name": document_label,
		"posting_date": date_label,
		"customer": party_label,
		"supplier": party_label,
		"party_name": party_label,
		"grand_total": "Grand Total",
		"quantity": "Quantity",
		"outstanding_amount": "Outstanding Amount",
		"status": "Status",
	}
	available_columns = ["document_name", "posting_date"]
	if has_party_column:
		available_columns.append("party_name")
	if any(row.get("quantity") not in (None, "", 0) for row in document_rows):
		available_columns.append("quantity")
	if any(row.get("grand_total") not in (None, "", 0) for row in document_rows):
		available_columns.append("grand_total")
	if any(row.get("outstanding_amount") not in (None, "", 0) for row in document_rows):
		available_columns.append("outstanding_amount")
	available_columns.append("status")
	selected_columns = requested_columns or available_columns
	selected_columns = [value for value in selected_columns if value in column_map]
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
		limited_rows = document_rows[:top_n]
		table_rows: List[List[str]] = []
		for row in limited_rows:
			out: List[str] = []
			for key in selected_columns:
				if key == "posting_date":
					out.append(_clean_text(row.get(key)))
				elif key == "status":
					out.append(_clean_text(row.get(key)))
				elif key in {"customer", "party_name"}:
					out.append(_clean_text(row.get(key) or row.get("party_name") or row.get("customer")))
				elif key == "document_name":
					out.append(_clean_text(row.get(key)))
				else:
					out.append(_amount_text(row.get(key)))
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
				"items": ["No matching governed documents were found for the current filters."],
			}
		)
	return title, blocks


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
		title, blocks = _inventory_blocks(artifact_contract)
	elif family_id == "product_profitability":
		title, blocks = _product_blocks(artifact_contract, response_overrides=response_overrides)
	elif family_id == "transaction_listing":
		title, blocks = _transaction_listing_blocks(artifact_contract)
	else:
		return FamilyRenderOutcome(
			status="render_not_available",
			errors=[f"No governed family renderer is defined for `{family_id}`."],
		)
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
