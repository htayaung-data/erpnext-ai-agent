from __future__ import annotations

import re
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.business_reasoning_policy import (
	composite_blocked_reasoning_boundary_answer,
	composite_blocked_reasoning_boundary_rendered_payload,
	composite_driver_analysis_answer,
	composite_driver_analysis_rendered_payload,
)
from ai_assistant_ui.qwen_chat.metadata import get_composite_family_spec
from ai_assistant_ui.qwen_chat.semantic_aliases import get_metric_label


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _normalize_text(value: Any) -> str:
	return " ".join(_clean_text(value).lower().replace("_", " ").split())


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _format_number(value: Any) -> str:
	number = _numeric(value)
	return f"{number:,.2f}".rstrip("0").rstrip(".")


def _format_metric_value(metric_key: str, value: Any, display_value: str = "") -> str:
	if _clean_text(display_value):
		return _clean_text(display_value)
	key = _clean_text(metric_key)
	if key.endswith("_ratio") or "utilization" in key or key.endswith("_percent"):
		number = _numeric(value)
		if -1.0 <= number <= 1.0:
			number *= 100
		return f"{_format_number(number)}%"
	if "amount" in key or "revenue" in key or "profit" in key or "value" in key:
		return f"{_format_number(value)} MMK"
	return _format_number(value)


def _ordinal_reference_index(message: str) -> int:
	normalized = _normalize_text(message)
	if not normalized:
		return -1
	ordinal_words = {
		"first": 1,
		"second": 2,
		"third": 3,
		"fourth": 4,
		"fifth": 5,
		"sixth": 6,
		"seventh": 7,
		"eighth": 8,
		"ninth": 9,
		"tenth": 10,
	}
	for word, value in ordinal_words.items():
		if re.search(rf"\b{re.escape(word)}\b", normalized):
			return value - 1
	for pattern in (
		r"\b(?:rank|row|number|no|no\.|#)\s*(\d{1,2})\b",
		r"\b(\d{1,2})(?:st|nd|rd|th)\b",
	):
		match = re.search(pattern, normalized)
		if not match:
			continue
		try:
			value = int(match.group(1))
		except (TypeError, ValueError):
			continue
		if value > 0:
			return value - 1
	return -1


def _source_composite_family_id(artifact_payload: Dict[str, Any]) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	filters = artifact.get("filters") if isinstance(artifact.get("filters"), dict) else {}
	return _clean_text(dimensions.get("source_composite_family_id") or filters.get("composite_family_id"))


def _source_composite_family_label(family_spec: Dict[str, Any], artifact_payload: Dict[str, Any]) -> str:
	dimensions = artifact_payload.get("dimensions") if isinstance(artifact_payload.get("dimensions"), dict) else {}
	return _clean_text(dimensions.get("source_composite_family_label") or family_spec.get("label") or "Composite View")


def _subject_alias(family_spec: Dict[str, Any], artifact_payload: Dict[str, Any]) -> str:
	dimensions = artifact_payload.get("dimensions") if isinstance(artifact_payload.get("dimensions"), dict) else {}
	alias = _clean_text(
		dimensions.get("entity_dimension")
		or family_spec.get("subject_alias_value")
		or family_spec.get("subject_alias")
		or family_spec.get("entity_dimension")
	)
	if alias:
		return alias.lower()
	return "row"


def _ranked_rows(artifact_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	sections = artifact_payload.get("sections") if isinstance(artifact_payload.get("sections"), dict) else {}
	return [dict(row) for row in (sections.get("ranked_rows") or []) if isinstance(row, dict)]


def _entity_label(row: Dict[str, Any]) -> str:
	return _clean_text(
		row.get("entity_name")
		or row.get("entity")
		or row.get("customer")
		or row.get("supplier")
		or row.get("item_name")
		or row.get("item_code")
	)


def _row_rank(row: Dict[str, Any], fallback_index: int) -> int:
	for key in ("rank", "row_rank", "position"):
		try:
			value = int(row.get(key) or 0)
		except (TypeError, ValueError):
			value = 0
		if value > 0:
			return value
	return fallback_index + 1


def _selected_ranked_row(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> Dict[str, Any]:
	rows = _ranked_rows(artifact_payload)
	if not rows:
		return {}
	ordinal_index = _ordinal_reference_index(raw_message)
	if ordinal_index >= 0:
		for index, row in enumerate(rows):
			if _row_rank(row, index) == ordinal_index + 1:
				return row
		if ordinal_index < len(rows):
			return rows[ordinal_index]
		return {}
	message_text = f" {_normalize_text(raw_message)} "
	named_matches = [
		row
		for row in rows
		if _entity_label(row) and f" {_normalize_text(_entity_label(row))} " in message_text
	]
	if len(named_matches) == 1:
		return named_matches[0]
	known_entities = [
		item
		for item in ((grounded_turn if isinstance(grounded_turn, dict) else {}).get("known_entities") or [])
		if isinstance(item, dict)
	]
	if len(known_entities) == 1:
		entity_key = _normalize_text(
			known_entities[0].get("code")
			or known_entities[0].get("entity_key")
			or known_entities[0].get("name")
			or known_entities[0].get("entity_label")
		)
		for row in rows:
			if entity_key and entity_key in {_normalize_text(_entity_label(row)), _normalize_text(row.get("entity_code"))}:
				return row
	if len(rows) == 1:
		return rows[0]
	return {}


def _message_requests_composite_evidence(message: str, family_spec: Dict[str, Any]) -> bool:
	normalized = _normalize_text(message)
	if not normalized:
		return False
	if re.search(r"\b(?:who|which|what)\s+should\b", normalized):
		return False
	if re.search(r"\b(why|explain|reason|because|breakdown|driver|basis)\b", normalized):
		return True
	for alias in family_spec.get("default_primary_trigger_aliases") or []:
		alias_text = _normalize_text(alias)
		if alias_text and re.search(rf"(^|[^a-z0-9]){re.escape(alias_text)}([^a-z0-9]|$)", normalized):
			return True
	for affordance in family_spec.get("followup_affordances") or []:
		affordance_text = _normalize_text(affordance)
		if affordance_text and any(token in normalized for token in affordance_text.split()):
			return True
	return False


def _message_requests_bucket_breakdown(message: str) -> bool:
	normalized = _normalize_text(message)
	if not normalized:
		return False
	return bool(
		re.search(r"\b(aging|ageing|bucket|buckets|due period|breakdown)\b", normalized)
		and re.search(r"\b(aging|ageing|bucket|buckets|due period)\b", normalized)
	)


def _metric_value(row: Dict[str, Any], metric_key: str) -> tuple[Any, str]:
	metric_values = row.get("metric_values") if isinstance(row.get("metric_values"), dict) else {}
	value_payload = metric_values.get(metric_key) if isinstance(metric_values.get(metric_key), dict) else {}
	if value_payload:
		return value_payload.get("value"), _clean_text(value_payload.get("display_value"))
	return row.get(metric_key), ""


def _metric_rows(
	*,
	row: Dict[str, Any],
	family_spec: Dict[str, Any],
	artifact_payload: Dict[str, Any],
) -> List[Dict[str, str]]:
	dimensions = artifact_payload.get("dimensions") if isinstance(artifact_payload.get("dimensions"), dict) else {}
	primary_metric = _clean_text(
		dimensions.get("source_composite_primary_metric_id")
		or family_spec.get("default_primary_metric")
	)
	secondary_metrics = [
		_clean_text(value)
		for value in (
			dimensions.get("source_composite_secondary_metric_ids")
			or family_spec.get("default_secondary_metrics")
			or family_spec.get("allowed_secondary_metrics")
			or []
		)
		if _clean_text(value)
	]
	metric_keys = list(dict.fromkeys([primary_metric] + secondary_metrics))
	out: List[Dict[str, str]] = []
	for metric_key in metric_keys:
		if not metric_key:
			continue
		value, display_value = _metric_value(row, metric_key)
		if value in (None, "") and not display_value:
			continue
		out.append(
			{
				"metric_key": metric_key,
				"label": get_metric_label(metric_key) or metric_key.replace("_", " ").title(),
				"value": _format_metric_value(metric_key, value, display_value),
			}
		)
	return out


def _bucket_rows(row: Dict[str, Any]) -> List[Dict[str, str]]:
	raw_rows = row.get("aging_buckets") if isinstance(row.get("aging_buckets"), list) else []
	out: List[Dict[str, str]] = []
	for item in raw_rows:
		if not isinstance(item, dict):
			continue
		bucket = _clean_text(item.get("bucket") or item.get("label"))
		if not bucket:
			continue
		out.append({"bucket": bucket, "amount": f"{_format_number(item.get('amount'))} MMK"})
	return out


def _normalized_bucket_label(value: Any) -> str:
	return _normalize_text(str(value or "").replace("–", "-").replace("_", " "))


def _bucket_is_over_30_days(bucket: Any) -> bool:
	normalized = _normalized_bucket_label(bucket)
	if not normalized or normalized in {"<0", "0-30", "0 30"}:
		return False
	return bool(
		normalized.startswith("31")
		or normalized.startswith("61")
		or normalized.startswith("91")
		or normalized.startswith("121")
		or "above" in normalized
	)


def _bucket_amount_total(row: Dict[str, Any], *, over_30_only: bool = False) -> float:
	total = 0.0
	for item in row.get("aging_buckets") or []:
		if not isinstance(item, dict):
			continue
		if over_30_only and not _bucket_is_over_30_days(item.get("bucket") or item.get("label")):
			continue
		total += _numeric(item.get("amount"))
	return total


def _bucket_amount_for_label(row: Dict[str, Any], label: str) -> float | None:
	target = _normalized_bucket_label(label)
	for item in row.get("aging_buckets") or []:
		if not isinstance(item, dict):
			continue
		if _normalized_bucket_label(item.get("bucket") or item.get("label")) == target:
			return _numeric(item.get("amount"))
	return None


def _bucket_breakdown_answer(
	*,
	raw_message: str,
	row: Dict[str, Any],
	family_label: str,
	as_of_date: str,
) -> str:
	if not _message_requests_bucket_breakdown(raw_message):
		return ""
	entity_label = _entity_label(row) or "the selected row"
	bucket_rows = _bucket_rows(row)
	date_phrase = f" as of {as_of_date}" if as_of_date else ""
	if not bucket_rows:
		return (
			f"I can identify {entity_label} in the current {family_label} result, but the answer above "
			f"does not expose bucket-level aging amounts for that selected row{date_phrase}.\n\n"
			"I won't fabricate bucket values from the aggregate row. Please open the customer detail or receivable aging view "
			"if you want a bucket-level refresh."
		)
	table_lines = [
		"| Aging Bucket | Amount (MMK) |",
		"| --- | --- |",
		*[f"| {item['bucket']} | {item['amount'].replace(' MMK', '')} |" for item in bucket_rows],
	]
	total = _bucket_amount_total(row)
	over_30_total = _bucket_amount_total(row, over_30_only=True)
	recent_due = _bucket_amount_for_label(row, "0-30")
	oldest_bucket = _bucket_amount_for_label(row, "121-Above")
	summary_lines = [
		f"- Total due across displayed buckets: {_format_number(total)} MMK.",
		f"- Overdue beyond 30 days: {_format_number(over_30_total)} MMK.",
	]
	if recent_due is not None:
		summary_lines.append(f"- 0-30 day bucket: {_format_number(recent_due)} MMK.")
	if oldest_bucket is not None:
		summary_lines.append(f"- 121+ day bucket: {_format_number(oldest_bucket)} MMK.")
	return (
		f"{entity_label} aging breakdown from the current {family_label} result{date_phrase}:\n\n"
		+ "\n".join(table_lines)
		+ "\n\nSummary:\n"
		+ "\n".join(summary_lines)
		+ "\n\n"
		"This is based only on the selected row above."
	)


def composite_ranked_row_direct_evidence_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	family_id = _source_composite_family_id(artifact)
	if not family_id:
		return ""
	family_spec = get_composite_family_spec(family_id)
	if str(family_spec.get("activation_state") or "").strip() != "active":
		return ""
	policy_boundary_answer = composite_blocked_reasoning_boundary_answer(
		raw_message=raw_message,
		artifact_payload=artifact,
		grounded_turn=grounded_turn,
	)
	if policy_boundary_answer:
		return policy_boundary_answer
	driver_answer = composite_driver_analysis_answer(
		raw_message=raw_message,
		artifact_payload=artifact,
		grounded_turn=grounded_turn,
	)
	if driver_answer:
		return driver_answer
	if not _message_requests_composite_evidence(raw_message, family_spec):
		return ""
	row = _selected_ranked_row(
		raw_message=raw_message,
		artifact_payload=artifact,
		grounded_turn=grounded_turn,
	)
	if not row:
		return ""
	family_label = _source_composite_family_label(family_spec, artifact)
	as_of_date = _clean_text((artifact.get("period") or {}).get("as_of_date") or (artifact.get("filters") or {}).get("as_of_date"))
	bucket_answer = _bucket_breakdown_answer(
		raw_message=raw_message,
		row=row,
		family_label=family_label,
		as_of_date=as_of_date,
	)
	if bucket_answer:
		return bucket_answer
	metric_rows = _metric_rows(row=row, family_spec=family_spec, artifact_payload=artifact)
	if not metric_rows:
		return ""
	entity_label = _entity_label(row) or "the selected row"
	rank = _row_rank(row, 0)
	metric_lines = "\n".join(f"- {item['label']}: {item['value']}" for item in metric_rows)
	date_phrase = f" as of {as_of_date}" if as_of_date else ""
	return (
		f"{entity_label} is highlighted in the {family_label} because it ranks #{rank} "
		f"in the current result{date_phrase}.\n\n"
		f"Key ERP facts:\n{metric_lines}\n\n"
		"This explanation is based only on the answer above. "
		"It is not a prediction, severity label, or collection recommendation."
	)


def composite_ranked_row_evidence_boundary_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	family_id = _source_composite_family_id(artifact)
	if not family_id:
		return ""
	family_spec = get_composite_family_spec(family_id)
	if str(family_spec.get("activation_state") or "").strip() != "active":
		return ""
	if not _message_requests_composite_evidence(raw_message, family_spec):
		return ""
	rows = _ranked_rows(artifact)
	if len(rows) <= 1:
		return ""
	if _selected_ranked_row(
		raw_message=raw_message,
		artifact_payload=artifact,
		grounded_turn=grounded_turn,
	):
		return ""
	family_label = _source_composite_family_label(family_spec, artifact)
	subject_alias = _subject_alias(family_spec, artifact)
	option_lines: List[str] = []
	for index, row in enumerate(rows[:5]):
		entity_label = _entity_label(row)
		if not entity_label:
			continue
		option_lines.append(f"- Rank {_row_rank(row, index)}: {entity_label}")
	if not option_lines:
		return ""
	extra_count = len(rows) - len(option_lines)
	if extra_count > 0:
		option_lines.append(f"- ...and {extra_count} more")
	choice_hint = f"which {subject_alias} or row you mean"
	return (
		f"I can explain that from the current {family_label} result, but I need {choice_hint}.\n\n"
		"Current options:\n"
		+ "\n".join(option_lines)
		+ "\n\n"
		f"For example, ask \"why is the first {subject_alias} highlighted?\" or \"explain rank 2\"."
	)


def composite_ranked_row_direct_evidence_rendered_payload(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> Dict[str, Any]:
	answer_text = composite_ranked_row_direct_evidence_answer(
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
	)
	if not answer_text:
		return {}
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	policy_payload = composite_blocked_reasoning_boundary_rendered_payload(
		raw_message=raw_message,
		artifact_payload=artifact,
		grounded_turn=grounded_turn,
	)
	if policy_payload:
		return policy_payload
	driver_payload = composite_driver_analysis_rendered_payload(
		raw_message=raw_message,
		artifact_payload=artifact,
		grounded_turn=grounded_turn,
	)
	if driver_payload:
		return driver_payload
	family_id = _source_composite_family_id(artifact)
	family_spec = get_composite_family_spec(family_id)
	row = _selected_ranked_row(
		raw_message=raw_message,
		artifact_payload=artifact,
		grounded_turn=grounded_turn,
	)
	metric_rows = _metric_rows(row=row, family_spec=family_spec, artifact_payload=artifact)
	bucket_rows = _bucket_rows(row) if _message_requests_bucket_breakdown(raw_message) else []
	blocks: List[Dict[str, Any]] = []
	if bucket_rows:
		blocks.append(
			{
				"block_type": "data_table",
				"title": "Aging Breakdown",
				"columns": ["Aging Bucket", "Amount (MMK)"],
				"rows": [[item["bucket"], item["amount"].replace(" MMK", "")] for item in bucket_rows],
			}
		)
	if metric_rows:
		blocks.append(
			{
				"block_type": "data_table",
				"title": "Current ERP Metrics",
				"columns": ["Metric", "Value"],
				"rows": [[item["label"], item["value"]] for item in metric_rows],
			}
		)
	blocks.append(
		{
			"block_type": "bullet_list",
			"title": "Decision Limit",
			"items": [
				"Uses only the facts shown above.",
				"Does not create prediction, severity, or collection recommendation labels.",
			],
		}
	)
	return {
		"type": "qwen_rendered_family_response_contract",
		"contract_version": "1.0",
		"request_id": _clean_text(artifact.get("request_id")),
		"family_id": _clean_text(artifact.get("family_id")),
		"renderer_id": "composite_ranked_row_direct_evidence",
		"rendering_policy": "deterministic",
		"title": f"Evidence for {_entity_label(row) or 'Selected Row'}",
		"answer_text": answer_text,
		"source_reports": [
			_clean_text(value)
			for value in (artifact.get("source_reports") or [])
			if _clean_text(value)
		],
		"blocks": blocks,
		"warnings": [
			_clean_text(value)
			for value in (artifact.get("warnings") or [])
			if _clean_text(value)
		],
	}
