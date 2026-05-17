from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.entity_period_aggregation_support import (
	list_entity_period_commercial_rows,
)


def list_customer_commercial_period_rows(
	*,
	report_name: str,
	company: str,
	from_date: str,
	to_date: str,
) -> List[Dict[str, Any]]:
	rows = list_entity_period_commercial_rows(
		report_name=report_name,
		company=company,
		from_date=from_date,
		to_date=to_date,
	)
	return [row for row in rows if str(row.get("entity_grain") or "").strip() == "customer"]
