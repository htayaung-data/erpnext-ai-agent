from __future__ import annotations

from typing import Iterable, List

from .policy_boundary_response import render_policy_boundary_text
from .policy_boundary_uniformity import build_policy_boundary_uniformity_contract


VISIBLE_CONTEXT_BOUNDARY_LANGUAGE_VERSION = "1.0"


def _clean_text(value: object) -> str:
	return str(value or "").strip()


def _plural(noun: str, count: int) -> str:
	if count == 1:
		return noun
	return f"{noun}s"


def _limited(values: Iterable[str], limit: int = 10) -> List[str]:
	return [_clean_text(value) for value in values if _clean_text(value)][:limit]


def render_missing_field_boundary(
	*,
	visible_field_labels: Iterable[str],
	missing_field_labels: Iterable[str],
) -> str:
	visible_labels = _limited(visible_field_labels, 8)
	missing_labels = _limited(missing_field_labels, 6)
	missing_count = len(missing_labels) or 1
	field_noun = "field" if missing_count == 1 else "fields"
	field_reference = "that field" if missing_count == 1 else "those fields"
	lines = [
		f"I can't verify that from this displayed result because the table does not include the requested {field_noun}.",
		"",
	]
	if visible_labels:
		lines.append(f"Visible evidence covers: {', '.join(visible_labels)}.")
	if missing_labels:
		lines.append(f"{field_noun.title()} needed: {', '.join(missing_labels)}.")
	lines.extend(
		[
			"",
			f"To answer safely, we need a governed result that includes {field_reference} or a filtered view that proves the condition.",
		]
	)
	return "\n".join(line for line in lines if line is not None).strip()


def render_prediction_boundary(
	*,
	rank_text: str,
	entity_label: str,
	metric_lines: Iterable[str],
) -> str:
	metrics = _limited(metric_lines, 12)
	contract = build_policy_boundary_uniformity_contract(
		route="visible_context_boundary_language",
		visible_authority_intent="prediction_boundary",
		visible_metric_lines=metrics,
	)
	return render_policy_boundary_text(
		contract,
		rank_text=rank_text,
		entity_label=entity_label,
		metric_lines=metrics,
	)


def render_recommendation_boundary(
	*,
	rank_text: str,
	entity_label: str,
	metric_lines: Iterable[str],
) -> str:
	metrics = _limited(metric_lines, 12)
	contract = build_policy_boundary_uniformity_contract(
		route="visible_context_boundary_language",
		visible_authority_intent="recommendation_boundary",
		visible_metric_lines=metrics,
	)
	return render_policy_boundary_text(
		contract,
		rank_text=rank_text,
		entity_label=entity_label,
		metric_lines=metrics,
	)


def render_causal_boundary(
	*,
	rank_text: str,
	entity_label: str,
	metric_lines: Iterable[str],
) -> str:
	metrics = _limited(metric_lines, 12)
	contract = build_policy_boundary_uniformity_contract(
		route="visible_context_boundary_language",
		visible_authority_intent="causal_boundary",
		visible_metric_lines=metrics,
	)
	return render_policy_boundary_text(
		contract,
		rank_text=rank_text,
		entity_label=entity_label,
		metric_lines=metrics,
	)


def render_row_clarification(
	*,
	options: Iterable[str],
) -> str:
	clean_options = _limited(options, 10)
	lines = [
		"I can continue, but the current result has multiple visible rows and no row is selected yet.",
	]
	if clean_options:
		lines.append("")
		lines.append("Visible rows:")
		for index, option in enumerate(clean_options, start=1):
			lines.append(f"- Rank {index}: {option}")
	lines.extend(
		[
			"",
			'Use a visible rank or row name, for example: "explain rank 2".',
		]
	)
	return "\n".join(lines).strip()


def render_out_of_range_rank(
	*,
	options: Iterable[str],
	requested_rank: int,
	available_count: int,
	row_label: str,
) -> str:
	clean_options = _limited(options, 10)
	count = max(0, int(available_count or len(clean_options) or 0))
	label = _clean_text(row_label) or "row"
	requested_text = f"rank {requested_rank}" if requested_rank else "that rank"
	lines = [
		f"The current result has only {count} visible {_plural(label, count)}, so there is no {requested_text}.",
	]
	if clean_options:
		lines.append("")
		lines.append("Available rows:")
		for index, option in enumerate(clean_options, start=1):
			lines.append(f"- Rank {index}: {option}")
	lines.extend(
		[
			"",
			"I can review any visible rank above, or you can ask for a broader result with more rows.",
		]
	)
	return "\n".join(lines).strip()
