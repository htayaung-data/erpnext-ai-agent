from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.compiler import _date_range_from_time_scope
from ai_assistant_ui.qwen_chat.context.message_history import latest_display_preferences
from ai_assistant_ui.qwen_chat.metadata import (
	get_composite_family_spec,
	report_capability_ids,
	resolve_followup_report_switch,
)
from ai_assistant_ui.qwen_chat.recovery_support import structured_governed_query_message
from ai_assistant_ui.qwen_chat.semantic_aliases import get_canonical_key, get_metric_label


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _metric_phrase(metric_id: str) -> str:
	value = _clean_text(metric_id)
	if value == "average_order_value":
		return "average order value"
	if value == "average_invoice_value":
		return "average invoice value"
	return value.replace("_", " ")


def _basis_context_phrase(basis: str) -> str:
	value = _clean_text(basis)
	if value == "sales_order":
		return "sales orders"
	if value == "sales_invoice":
		return "sales invoices"
	return value.replace("_", " ")


def _time_scope_from_range(from_date: str, to_date: str, fallback: str = "") -> str:
	start = _clean_text(from_date)
	end = _clean_text(to_date)
	if start and end:
		for candidate in ("last_month", "current_fiscal_year_to_date", "last_year"):
			candidate_start, candidate_end = _date_range_from_time_scope(candidate)
			if candidate_start == start and candidate_end == end:
				return candidate
	return _clean_text(fallback)


def _time_scope_phrase(time_scope: str) -> str:
	value = _clean_text(time_scope)
	if value == "last_month":
		return "last month"
	if value == "current_fiscal_year_to_date":
		return "current fiscal year to date"
	if value == "last_year":
		return "last year"
	return value.replace("_", " ")


def _composite_secondary_metric_ids(
	*,
	composite_family_id: str,
	requested_columns: List[str],
	primary_metric_id: str,
	fallback_secondary_metric_ids: List[str],
) -> List[str]:
	family_spec = get_composite_family_spec(composite_family_id)
	metric_semantic_key_map = (
		family_spec.get("metric_semantic_key_map")
		if isinstance(family_spec.get("metric_semantic_key_map"), dict)
		else {}
	)

	def _resolve_metric_id(value: str) -> str:
		clean = _clean_text(value)
		if not clean:
			return ""
		canonical = _clean_text(get_canonical_key(clean, dimension_or_metric="metric") or clean)
		canonical_key = canonical.lower().replace(" ", "_")
		for metric_id, semantic_keys in metric_semantic_key_map.items():
			candidates = {
				_clean_text(metric_id).lower().replace(" ", "_"),
				*{
					_clean_text(get_canonical_key(item, dimension_or_metric="metric") or item).lower().replace(" ", "_")
					for item in (semantic_keys or [])
					if _clean_text(item)
				},
			}
			if canonical_key in candidates:
				return _clean_text(metric_id)
		return canonical_key

	primary = _clean_text(primary_metric_id)
	out: List[str] = []
	for value in requested_columns:
		clean = _resolve_metric_id(value)
		if not clean or clean in {"entity", "entity_code", primary}:
			continue
		if clean not in out:
			out.append(clean)
	if out:
		return out
	for value in fallback_secondary_metric_ids:
		clean = _resolve_metric_id(value)
		if clean and clean != primary and clean not in out:
			out.append(clean)
	return out


def _compile_composite_family_requery_message(
	*,
	composite_family_id: str,
	composite_subject_alias: str,
	composite_basis: str,
	primary_metric_id: str,
	secondary_metric_ids: List[str],
	time_scope: str,
	target_limit: int,
) -> str:
	family_spec = get_composite_family_spec(composite_family_id)
	subject = _clean_text(composite_subject_alias) or _clean_text(family_spec.get("subject_alias_value")) or "item"
	limit_phrase = f"top {target_limit}" if int(max(0, target_limit or 0)) > 0 else "top"
	parts = [f"show {limit_phrase} {subject}s by {_metric_phrase(primary_metric_id)}"]
	if composite_basis:
		parts.append(f"for {_basis_context_phrase(composite_basis)}")
	time_scope_phrase = _time_scope_phrase(time_scope)
	if time_scope_phrase:
		parts.append(time_scope_phrase)
	if secondary_metric_ids:
		parts.append("with " + " and ".join(_metric_phrase(metric_id) for metric_id in secondary_metric_ids))
	return " ".join(part for part in parts if part).strip()


def _compile_transaction_listing_requery_message(
	*,
	raw_message: str,
	source_report: str,
	target_report: str,
	target_capability_id: str,
	company: str,
	requested_time_scope: str,
	preserve_prior_date_scope: bool,
	report_date: str,
	from_date: str,
	to_date: str,
	target_dimension: str,
	target_limit: int,
	requested_modes: List[str],
	prefs: Dict[str, Any],
) -> str:
	parts: List[str] = []
	if target_report:
		parts.append(f"Use the report `{target_report}`.")
	else:
		parts.append("Keep the governed business context from the latest grounded answer.")
		if source_report:
			parts.append(f"Latest grounded report: `{source_report}`.")
		if target_capability_id:
			parts.append(f"Use the governed capability `{target_capability_id}` if needed to satisfy the request.")
	if company:
		parts.append(f'Use company "{company}".')
	if requested_time_scope == "last_month":
		parts.append("Use the last month date range.")
	elif requested_time_scope == "last_year":
		parts.append("Use the last year date range.")
	elif requested_time_scope == "current_period":
		parts.append("Use the current month to date.")
	elif requested_time_scope == "current_fiscal_year_to_date":
		parts.append("Use the current fiscal year to date range.")
	elif requested_time_scope == "as_of_today":
		parts.append("Use the current date context as of today.")
	elif requested_time_scope == "all_period":
		parts.append("Use the full available time range.")
	elif preserve_prior_date_scope and from_date and to_date:
		parts.append(f"Use the date range from {from_date} to {to_date}.")
	elif preserve_prior_date_scope and report_date:
		parts.append(f"Use report_date {report_date}.")
	if "filter_refinement" in set(requested_modes) and target_dimension:
		parts.append(f"Apply a governed filter refinement on `{target_dimension}` if the report exposes it.")
	if target_limit > 0:
		parts.append(f"Use a row limit of {target_limit} rows.")
	if prefs.get("million"):
		parts.append("Present monetary amounts in MMK Million.")
	if prefs.get("table"):
		parts.append("Present the result as a table.")
	parts.append(f"User request: {str(raw_message or '').strip()}")
	return " ".join(part for part in parts if part).strip()


def compile_capability_requery_message(
	session_doc,
	*,
	raw_message: str,
	followup_resolution,
	grounded_turn: Dict[str, Any],
	continuation_contract=None,
) -> str:
	source_report = str(grounded_turn.get("source_name") or "").strip()
	switch = resolve_followup_report_switch(
		getattr(followup_resolution, "requested_modes", []) or [],
		source_report,
	)
	target_report = str(getattr(followup_resolution, "target_report", "") or switch.get("target_report") or "").strip()

	filters = grounded_turn.get("filters") if isinstance(grounded_turn.get("filters"), dict) else {}
	date_range = grounded_turn.get("date_range") if isinstance(grounded_turn.get("date_range"), dict) else {}
	company = str(filters.get("company") or grounded_turn.get("company") or "").strip()
	report_date = str(date_range.get("report_date") or filters.get("report_date") or "").strip()
	from_date = str(date_range.get("from_date") or filters.get("from_date") or "").strip()
	to_date = str(date_range.get("to_date") or filters.get("to_date") or "").strip()
	requested_time_scope = str(getattr(followup_resolution, "requested_time_scope", "") or "").strip()
	target_dimension = str(getattr(followup_resolution, "target_dimension", "") or "").strip()
	target_limit = int(max(0, getattr(followup_resolution, "target_limit", 0) or 0))
	target_metric = str(getattr(followup_resolution, "target_metric", "") or "").strip()
	target_capability_id = str(getattr(followup_resolution, "target_capability_id", "") or "").strip()
	requested_modes = [
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_modes", []) or [])
		if str(value or "").strip()
	]
	preserved_dimension = str(getattr(continuation_contract, "preserved_dimension", "") or "").strip()
	preserved_metric_key = str(getattr(continuation_contract, "preserved_metric_key", "") or "").strip()
	preserved_requested_columns = [
		str(value or "").strip()
		for value in (
			getattr(continuation_contract, "preserved_requested_columns", [])
			or getattr(continuation_contract, "source_requested_columns", [])
			or []
		)
		if str(value or "").strip()
	]
	preserved_limit = int(max(0, getattr(continuation_contract, "preserved_limit", 0) or 0))
	preserved_entities = [
		str(value or "").strip()
		for value in (getattr(continuation_contract, "preserved_entities", []) or [])
		if str(value or "").strip()
	]
	preserve_rank_membership = bool(getattr(continuation_contract, "preserve_rank_membership", False))
	preserve_rank_order = bool(getattr(continuation_contract, "preserve_rank_order", False))
	preserve_prior_date_scope = bool(getattr(continuation_contract, "preserve_date_context", False))
	source_composite_family_id = str(getattr(continuation_contract, "source_composite_family_id", "") or "").strip()
	source_composite_subject_alias = str(getattr(continuation_contract, "source_composite_subject_alias", "") or "").strip()
	source_composite_basis = str(getattr(continuation_contract, "source_composite_basis", "") or "").strip()
	source_composite_primary_metric_id = str(
		getattr(continuation_contract, "source_composite_primary_metric_id", "") or ""
	).strip()
	source_composite_secondary_metric_ids = [
		str(value or "").strip()
		for value in (getattr(continuation_contract, "source_composite_secondary_metric_ids", []) or [])
		if str(value or "").strip()
	]
	source_composite_time_scope = str(getattr(continuation_contract, "source_composite_time_scope", "") or "").strip()
	requested_columns = [
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_columns", []) or [])
		if str(value or "").strip()
	]
	if not requested_columns and bool(getattr(continuation_contract, "preserve_projection_shape", False)):
		requested_columns = list(preserved_requested_columns)
	effective_capability_id = target_capability_id
	if not effective_capability_id:
		report_for_capability = target_report or source_report
		effective_capability_id = str((report_capability_ids(report_for_capability) or [""])[0] or "").strip()
	prefs = latest_display_preferences(session_doc, requested_modes=getattr(followup_resolution, "requested_modes", []) or [])
	hint = str(switch.get("requery_prompt_hint") or "").strip()

	target_metric_canonical = (
		get_canonical_key(target_metric, capability_id=effective_capability_id, dimension_or_metric="metric")
		if target_metric
		else None
	)
	extra_metric_labels: List[str] = []
	for value in requested_columns:
		canonical_metric = get_canonical_key(
			value,
			capability_id=effective_capability_id,
			dimension_or_metric="metric",
		)
		if not canonical_metric:
			continue
		if target_metric_canonical and canonical_metric == target_metric_canonical:
			continue
		label = get_metric_label(canonical_metric)
		if label and label not in extra_metric_labels:
			extra_metric_labels.append(label)

	source_family_id = str(
		getattr(continuation_contract, "source_family_id", "")
		or grounded_turn.get("artifact_family_id")
		or ""
	).strip()
	primary_metric_for_query = str(target_metric or "").strip()
	if not primary_metric_for_query:
		for value in requested_columns:
			canonical_metric = get_canonical_key(
				value,
				capability_id=effective_capability_id or None,
				dimension_or_metric="metric",
			)
			if canonical_metric:
				primary_metric_for_query = str(get_metric_label(canonical_metric) or value or "").strip()
				break
	if not primary_metric_for_query and preserved_metric_key:
		primary_metric_for_query = str(get_metric_label(preserved_metric_key) or preserved_metric_key or "").strip()
	time_phrase = ""
	if requested_time_scope == "last_month":
		time_phrase = " for last month"
	elif requested_time_scope == "last_year":
		time_phrase = " for last year"
	elif requested_time_scope == "current_period":
		time_phrase = " for the current month"
	elif requested_time_scope == "current_fiscal_year_to_date":
		time_phrase = " for the current fiscal year to date"
	elif requested_time_scope == "as_of_today":
		time_phrase = " as of today"
	elif requested_time_scope == "all_period":
		time_phrase = " for the full available time range"
	elif preserve_prior_date_scope and report_date:
		time_phrase = f" as of {report_date}"
	elif preserve_prior_date_scope and from_date and to_date:
		time_phrase = f" from {from_date} to {to_date}"
	composite_time_scope = requested_time_scope or _time_scope_from_range(
		from_date,
		to_date,
		fallback=source_composite_time_scope,
	)
	if source_composite_family_id and set(requested_modes).intersection(
		{"sort_or_limit", "metric_refinement", "column_refinement", "time_scope_restatement"}
	):
		composite_primary_metric_target = (
			target_metric
			if "metric_refinement" in set(requested_modes)
			else ""
		)
		composite_primary_metric_id = _clean_text(
			composite_primary_metric_target
			or source_composite_primary_metric_id
			or preserved_metric_key
			or getattr(continuation_contract, "source_metric_key", "")
			or ""
		)
		composite_secondary_metric_ids = _composite_secondary_metric_ids(
			composite_family_id=source_composite_family_id,
			requested_columns=requested_columns or preserved_requested_columns,
			primary_metric_id=composite_primary_metric_id,
			fallback_secondary_metric_ids=source_composite_secondary_metric_ids,
		)
		composite_message = _compile_composite_family_requery_message(
			composite_family_id=source_composite_family_id,
			composite_subject_alias=source_composite_subject_alias,
			composite_basis=source_composite_basis or str(filters.get("basis") or "").strip(),
			primary_metric_id=composite_primary_metric_id,
			secondary_metric_ids=composite_secondary_metric_ids,
			time_scope=composite_time_scope,
			target_limit=target_limit or preserved_limit,
		)
		if composite_message:
			return composite_message
	if (
		source_family_id == "ranking_analytics"
		and primary_metric_for_query
		and {"metric_refinement", "column_refinement", "sort_or_limit"}.intersection(set(requested_modes))
	):
		structured_query = structured_governed_query_message(
			requested_top_n=target_limit or preserved_limit,
			dimension=target_dimension or preserved_dimension,
			metric=primary_metric_for_query,
			time_phrase=time_phrase,
			report_name=target_report or source_report,
			capability_id=effective_capability_id,
		)
		if structured_query:
			return structured_query
	if source_family_id == "transaction_listing":
		return _compile_transaction_listing_requery_message(
			raw_message=raw_message,
			source_report=source_report,
			target_report=target_report,
			target_capability_id=target_capability_id,
			company=company,
			requested_time_scope=requested_time_scope,
			preserve_prior_date_scope=preserve_prior_date_scope,
			report_date=report_date,
			from_date=from_date,
			to_date=to_date,
			target_dimension=target_dimension,
			target_limit=target_limit,
			requested_modes=requested_modes,
			prefs=prefs,
		)

	parts: List[str] = []
	if target_report:
		parts.append(f"Use the report `{target_report}`.")
	else:
		parts.append("Keep the governed business context from the latest grounded answer.")
		if source_report:
			parts.append(f"Latest grounded report: `{source_report}`.")
		if target_capability_id:
			parts.append(f"Use the governed capability `{target_capability_id}` if needed to satisfy the request.")
	if company:
		parts.append(f'Use company "{company}".')
	if requested_time_scope == "last_month":
		parts.append("Use the last month date range.")
	elif requested_time_scope == "last_year":
		parts.append("Use the last year date range.")
	elif requested_time_scope == "current_period":
		parts.append("Use the current month to date.")
	elif requested_time_scope == "current_fiscal_year_to_date":
		parts.append("Use the current fiscal year to date range.")
	elif requested_time_scope == "as_of_today":
		parts.append("Use the current date context as of today.")
	elif requested_time_scope == "all_period":
		parts.append("Use the full available time range.")
	elif preserve_prior_date_scope and from_date and to_date:
		parts.append(f"Use the date range from {from_date} to {to_date}.")
	elif preserve_prior_date_scope and report_date:
		parts.append(f"Use report_date {report_date}.")
	if target_dimension:
		if "filter_refinement" in set(requested_modes):
			parts.append(f"Apply a governed filter refinement on `{target_dimension}` if the report exposes it.")
		else:
			parts.append(f"Return the result grouped or broken down by `{target_dimension}` if supported.")
	elif preserved_dimension:
		parts.append(f"Preserve the current entity dimension `{preserved_dimension}`.")
	if target_limit > 0:
		parts.append(f"Keep the same ranking scope and return only the top {target_limit} ranked rows.")
	elif preserved_limit > 0:
		parts.append(f"Keep the same ranking scope and return only the top {preserved_limit} ranked rows.")
	if target_metric:
		parts.append(f"Prioritize the metric `{target_metric}`.")
	elif preserved_metric_key:
		parts.append(f"Preserve the primary governed metric `{preserved_metric_key}`.")
	if extra_metric_labels:
		parts.append("Also include these governed metrics if supported: " + ", ".join(f"`{label}`" for label in extra_metric_labels) + ".")
	if preserve_rank_membership and preserved_entities:
		entity_text = ", ".join(f"`{value}`" for value in preserved_entities[:15])
		parts.append("Preserve the exact current ranked entities when enriching the result: " + entity_text + ".")
	if preserve_rank_order:
		parts.append("Preserve the existing ranking order from the latest grounded artifact unless the user explicitly changes it.")
	if requested_columns:
		parts.append("Return these columns if available: " + ", ".join(requested_columns) + ".")
	if requested_modes:
		parts.append("Requested follow-up transforms: " + ", ".join(requested_modes) + ".")
	if hint:
		parts.append(hint)
	if prefs.get("million"):
		parts.append("Present all amounts in MMK Million.")
	if prefs.get("table"):
		parts.append("Return the result as a table.")
	parts.append(f"User request: {str(raw_message or '').strip()}")
	return " ".join(part for part in parts if part).strip()
