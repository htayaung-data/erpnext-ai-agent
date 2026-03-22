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


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


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


def _amount_text(value: Any, currency: str = "") -> str:
	number = _float_value(value)
	if abs(number - round(number)) < 0.005:
		formatted = f"{number:,.0f}"
	else:
		formatted = f"{number:,.2f}"
	clean_currency = _clean_text(currency)
	return f"{formatted} {clean_currency}".strip()


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
				"columns": [party_label, "Outstanding", "Over 121 Days"],
				"rows": [
					[
						_clean_text(item.get("party")),
						_amount_text(item.get("outstanding"), _clean_text(item.get("currency") or currency)),
						_amount_text(item.get("bucket_121_above"), _clean_text(item.get("currency") or currency)),
					]
					for item in top_parties
				],
			}
		)
	return title, blocks


def _ranking_blocks(artifact: NormalizedFamilyArtifactContract) -> tuple[str, List[Dict[str, Any]]]:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	sections = artifact.sections if isinstance(artifact.sections, dict) else {}
	metric_label = _clean_text(dimensions.get("primary_metric_label")) or "Primary Metric"
	entity_label = _clean_text(dimensions.get("entity_dimension")) or "Entity"
	title = _title_with_period(f"Top {entity_label}s by {metric_label}", artifact.period)
	ranked_rows = _clean_rows(sections.get("ranked_rows"))[:10]
	summary = _clean_rows(sections.get("summary"))
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
		},
	]
	if ranked_rows:
		blocks.append(
			{
				"block_type": "data_table",
				"title": "Top Ranked Rows",
				"columns": ["Rank", entity_label, metric_label],
				"rows": [
					[
						str(int(_float_value(item.get("rank")) or (index + 1))),
						_clean_text(item.get("entity_name") or item.get("entity")),
						_amount_text(item.get(dimensions.get("primary_metric_key"))),
					]
					for index, item in enumerate(ranked_rows)
				],
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


def _product_blocks(artifact: NormalizedFamilyArtifactContract) -> tuple[str, List[Dict[str, Any]]]:
	dimensions = artifact.dimensions if isinstance(artifact.dimensions, dict) else {}
	sections = artifact.sections if isinstance(artifact.sections, dict) else {}
	metric_key = _clean_text(dimensions.get("primary_metric_key"))
	metric_label = _clean_text(dimensions.get("primary_metric_label")) or "Primary Metric"
	title = _title_with_period("Product Performance and Profitability", artifact.period)
	summary = _clean_rows(sections.get("summary"))
	product_rows = _clean_rows(sections.get("product_rows"))[:10]
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
		blocks.append(
			{
				"block_type": "data_table",
				"title": "Top Products",
				"columns": ["Product", metric_label, "Sales Amount", "Gross Profit %"],
				"rows": [
					[
						_clean_text(item.get("item_name") or item.get("item") or item.get("item_code")),
						_ratio_text(item.get(metric_key)) if metric_key == "gross_profit_percent" else _amount_text(item.get(metric_key)),
						_amount_text(item.get("sales_amount")),
						_ratio_text(item.get("gross_profit_percent")) if item.get("gross_profit_percent") not in (None, "") else "",
					]
					for item in product_rows
				],
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
		title, blocks = _ranking_blocks(artifact_contract)
	elif family_id == "trend_analytics":
		title, blocks = _trend_blocks(artifact_contract)
	elif family_id == "inventory_snapshot":
		title, blocks = _inventory_blocks(artifact_contract)
	elif family_id == "product_profitability":
		title, blocks = _product_blocks(artifact_contract)
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
