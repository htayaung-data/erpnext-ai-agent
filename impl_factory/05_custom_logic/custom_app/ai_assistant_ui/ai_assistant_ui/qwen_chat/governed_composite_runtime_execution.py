from __future__ import annotations

import datetime as dt
import re
from typing import Any, Dict, List, Tuple

from ai_assistant_ui.qwen_chat.business_definition_state import (
	resolve_business_definition_state,
	resolve_governed_formula_state,
)
from ai_assistant_ui.qwen_chat.compiler import _date_range_from_time_scope
from ai_assistant_ui.qwen_chat.composite_artifact_state import (
	CompositeArtifactResolutionContract,
	CompositeAssemblyAdapterContract,
	CompositeFamilyResolutionContract,
	build_composite_assembly_contract_from_spec,
	build_composite_governed_artifact_contract,
	resolve_composite_artifact_resolution,
	resolve_composite_family_resolution,
)
from ai_assistant_ui.qwen_chat.contracts import (
	FrontDoorIntentGateContract,
	GroundedTurnContext,
	build_clarification_signal_contract,
	build_normalized_family_artifact_contract,
	detect_language,
)
from ai_assistant_ui.qwen_chat.analytical_scope_policy import (
	apply_analytical_scope_runtime_policy,
)
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response
from ai_assistant_ui.qwen_chat.clarification_translation import (
	render_shared_choice_list_clarification,
)
from ai_assistant_ui.qwen_chat.defaults_repository import single_company_name
from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import (
	SemanticFrontDoorIntent,
	SemanticFrontDoorResult,
)
from ai_assistant_ui.qwen_chat.governed_kpi_execution_state import (
	GovernedKpiRankingArtifactContract,
	resolve_governed_kpi_execution_state,
)
from ai_assistant_ui.qwen_chat.metadata import (
	get_composite_artifact_spec,
	get_composite_assembly_spec,
	get_composite_compatibility_spec,
	get_frontdoor_intent_spec,
	get_governed_kpi_execution_spec,
	get_report_spec,
	list_composite_family_specs,
	list_semantic_resolution_alias_entries,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import get_aliases
from ai_assistant_ui.qwen_chat.semantic_resolution_registry import best_semantic_slot_alias
from ai_assistant_ui.qwen_chat.runtime_support import tool_trace_payload
from ai_assistant_ui.qwen_chat.composite_subject_support import (
	composite_entity_dimension_label,
)
from ai_assistant_ui.qwen_chat.composite_row_support import (
	composite_join_key_label,
	composite_row_entity_code,
	composite_row_identity_value,
	composite_row_join_key_payload,
	composite_row_join_key_tuple,
)
from ai_assistant_ui.qwen_chat.item_product_support import normalize_item_product_grain


_GENERIC_RANKING_REQUEST_PATTERN = re.compile(
	r"\b(top|highest|lowest|ranking|rank|bottom|least|priority|prioritize|prioritise)\b",
	re.IGNORECASE,
)
_DETAIL_REQUEST_PATTERN = re.compile(
	r"\b(how was|how is|calculated|calculate|formula|basis|show governed basis|explain calculation|assembled)\b",
	re.IGNORECASE,
)
_PERIOD_SCOPE_ORDER = (
	"last_month",
	"current_fiscal_year_to_date",
	"last_year",
)
_CLARIFICATION_PRIORITY = (
	"primary_sort_metric",
	"basis",
	"scope",
)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def current_date_iso() -> str:
	return dt.date.today().isoformat()


def _normalize_text(value: Any) -> str:
	return " ".join(_clean_text(value).lower().split())


def _singularize_token(token: str) -> str:
	clean = _clean_text(token).lower()
	if len(clean) > 4 and clean.endswith("ies"):
		return clean[:-3] + "y"
	if len(clean) > 3 and clean.endswith("ses"):
		return clean[:-2]
	if len(clean) > 3 and clean.endswith("s") and not clean.endswith("ss"):
		return clean[:-1]
	return clean


def _alias_variants(value: str) -> List[str]:
	clean = _clean_text(value).replace("_", " ")
	if not clean:
		return []
	normalized = " ".join(clean.lower().split())
	singularized = " ".join(
		_singularize_token(part)
		for part in normalized.split()
		if _singularize_token(part)
	)
	out: List[str] = []
	for candidate in (normalized, singularized):
		candidate_value = _clean_text(candidate)
		if candidate_value and candidate_value not in out:
			out.append(candidate_value)
	return out


def _money(value: Any) -> str:
	try:
		numeric = float(value or 0.0)
	except Exception:
		numeric = 0.0
	return f"{numeric:,.2f}".rstrip("0").rstrip(".")


def _count_text(value: Any) -> str:
	try:
		numeric = float(value or 0.0)
	except Exception:
		numeric = 0.0
	if abs(numeric - int(numeric)) < 0.000001:
		return f"{int(numeric):,}"
	return f"{numeric:,.2f}".rstrip("0").rstrip(".")


def _current_company_name(explicit_company_name: str) -> str:
	return _clean_text(explicit_company_name) or _clean_text(single_company_name())


def _extract_canonical_alias(slot_name: str, message: str) -> str:
	return best_semantic_slot_alias(slot_name, message)


def _extract_period_time_scope(message: str) -> str:
	value = _extract_canonical_alias("time_scope", message)
	return value if value in _PERIOD_SCOPE_ORDER else ""


def _extract_as_of_date_scope(message: str) -> str:
	explicit_iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", _clean_text(message))
	if explicit_iso_match:
		return _clean_text(explicit_iso_match.group(1))
	if _extract_canonical_alias("time_scope", message) == "as_of_today":
		return current_date_iso()
	return ""


def _extract_listing_view_basis(message: str) -> str:
	return _extract_canonical_alias("listing_view", message)


def _extract_family_basis(message: str, family_spec: Dict[str, Any]) -> str:
	supported_basis_values = [
		_clean_text(value)
		for value in family_spec.get("supported_variation_values", {}).get("basis", []) or []
		if _clean_text(value)
	]
	resolved_basis = _extract_listing_view_basis(message)
	if resolved_basis and resolved_basis in supported_basis_values:
		return resolved_basis
	normalized_message = _normalize_text(message)
	if not normalized_message:
		return ""
	for basis in supported_basis_values:
		basis_value = _clean_text(basis)
		if not basis_value:
			continue
		for alias in _alias_variants(basis_value) + _alias_variants(_basis_context_phrase(basis_value)) + _alias_variants(_basis_option_label(basis_value)):
			alias_text = _normalize_text(alias)
			if not alias_text:
				continue
			pattern = r"(^|[^a-z0-9])(" + re.escape(alias_text) + r")([^a-z0-9]|$)"
			if re.search(pattern, normalized_message):
				return basis_value
	return ""


def _ranking_subject(message: str) -> str:
	return _extract_canonical_alias("ranking_subject", message)


def _family_subject_requested(message: str, family_spec: Dict[str, Any]) -> bool:
	subject = _clean_text(family_spec.get("subject_alias_value"))
	normalized_message = _normalize_text(message)
	if not subject or not normalized_message:
		return False
	for alias in _alias_variants(subject) + _alias_variants(f"{subject}s"):
		alias_text = _normalize_text(alias)
		if not alias_text:
			continue
		pattern = r"(^|[^a-z0-9])(" + re.escape(alias_text) + r")([^a-z0-9]|$)"
		if re.search(pattern, normalized_message):
			return True
	return False


def _requested_top_n(message: str, default_limit: int = 10) -> int:
	match = re.search(r"\btop\s+(\d{1,3})\b", _normalize_text(message))
	if not match:
		return default_limit
	try:
		return max(1, min(int(match.group(1)), 100))
	except Exception:
		return default_limit


def _sort_direction_from_message(message: str, default_direction: str = "desc") -> str:
	normalized_message = _normalize_text(message)
	if re.search(r"\b(lowest|bottom|least)\b", normalized_message, re.IGNORECASE):
		return "asc"
	return _clean_text(default_direction) or "desc"


def _has_ranking_intent(message: str) -> bool:
	return bool(_GENERIC_RANKING_REQUEST_PATTERN.search(_normalize_text(message)))


def _runtime_detail_requested(message: str) -> bool:
	return bool(_DETAIL_REQUEST_PATTERN.search(_normalize_text(message)))


def _metric_alias_positions(message: str, semantic_keys: List[str]) -> List[int]:
	normalized_message = _normalize_text(message)
	if not normalized_message:
		return []
	positions: List[int] = []
	for semantic_key in semantic_keys:
		for alias in get_aliases(semantic_key):
			alias_text = _normalize_text(alias)
			if not alias_text:
				continue
			pattern = r"(^|[^a-z0-9])(" + re.escape(alias_text) + r")([^a-z0-9]|$)"
			for match in re.finditer(pattern, normalized_message):
				positions.append(match.start(2))
	return sorted(positions)


def _slot_alias_spans(slot_name: str, message: str) -> List[Tuple[int, int]]:
	normalized_message = _normalize_text(message)
	if not normalized_message:
		return []
	spans: List[Tuple[int, int]] = []
	for entry in list_semantic_resolution_alias_entries(slot_name):
		for alias in (entry.get("aliases") or []):
			alias_text = _normalize_text(alias)
			if not alias_text:
				continue
			pattern = r"(^|[^a-z0-9])(" + re.escape(alias_text) + r")([^a-z0-9]|$)"
			for match in re.finditer(pattern, normalized_message):
				spans.append((match.start(2), match.end(2)))
	return spans


def _family_metric_positions(message: str, family_spec: Dict[str, Any]) -> Dict[str, List[int]]:
	metric_map = dict(family_spec.get("metric_semantic_key_map") or {})
	basis_spans = _slot_alias_spans("listing_view", message)
	positions: Dict[str, List[int]] = {}
	for metric_id, semantic_keys in metric_map.items():
		metric_positions = [
			position
			for position in _metric_alias_positions(
				message,
				[str(value or "").strip() for value in (semantic_keys or []) if str(value or "").strip()],
			)
			if not any(span_start <= position < span_end for span_start, span_end in basis_spans)
		]
		if metric_positions:
			positions[str(metric_id or "").strip()] = metric_positions
	return positions


def _extract_primary_metric(message: str, family_spec: Dict[str, Any]) -> str:
	metric_positions = _family_metric_positions(message, family_spec)
	allowed_primary = [
		_clean_text(value)
		for value in (family_spec.get("allowed_primary_metrics") or [])
		if _clean_text(value)
	]
	candidates = {metric_id: positions for metric_id, positions in metric_positions.items() if metric_id in allowed_primary}
	if not candidates:
		return ""
	normalized_message = _normalize_text(message)
	by_match = list(re.finditer(r"\bby\b", normalized_message, re.IGNORECASE))
	if by_match:
		last_by_end = by_match[-1].end()
		after_by = {
			metric_id: [position for position in positions if position >= last_by_end]
			for metric_id, positions in candidates.items()
		}
		after_by = {metric_id: positions for metric_id, positions in after_by.items() if positions}
		if len(after_by) == 1:
			return next(iter(after_by.keys()))
		if after_by:
			return sorted(after_by.items(), key=lambda item: min(item[1]))[0][0]
	if len(candidates) == 1:
		return next(iter(candidates.keys()))
	return ""


def _extract_secondary_metrics(
	message: str,
	family_spec: Dict[str, Any],
	primary_metric_id: str,
) -> List[str]:
	metric_positions = _family_metric_positions(message, family_spec)
	allowed_secondary = [
		_clean_text(value)
		for value in (family_spec.get("allowed_secondary_metrics") or [])
		if _clean_text(value)
	]
	out: List[str] = []
	for metric_id in allowed_secondary:
		if metric_id == _clean_text(primary_metric_id):
			continue
		if metric_id in metric_positions and metric_id not in out:
			out.append(metric_id)
	return out


def _default_primary_metric_from_family_spec(family_spec: Dict[str, Any]) -> str:
	default_primary_metric = _clean_text(family_spec.get("default_primary_metric"))
	allowed_primary = {
		_clean_text(value)
		for value in (family_spec.get("allowed_primary_metrics") or [])
		if _clean_text(value)
	}
	return default_primary_metric if default_primary_metric in allowed_primary else ""


def _default_secondary_metrics_from_family_spec(
	family_spec: Dict[str, Any],
	primary_metric_id: str,
) -> List[str]:
	allowed_secondary = {
		_clean_text(value)
		for value in (family_spec.get("allowed_secondary_metrics") or [])
		if _clean_text(value)
	}
	out: List[str] = []
	for value in family_spec.get("default_secondary_metrics") or []:
		metric_id = _clean_text(value)
		if metric_id and metric_id != _clean_text(primary_metric_id) and metric_id in allowed_secondary and metric_id not in out:
			out.append(metric_id)
	return out


def _family_default_trigger_requested(message: str, family_spec: Dict[str, Any]) -> bool:
	normalized_message = _normalize_text(message)
	if not normalized_message:
		return False
	for alias in family_spec.get("default_primary_trigger_aliases") or []:
		alias_text = _normalize_text(alias)
		if not alias_text:
			continue
		pattern = r"(^|[^a-z0-9])(" + re.escape(alias_text) + r")([^a-z0-9]|$)"
		if re.search(pattern, normalized_message):
			return True
	return False


def _as_of_requested_scope(
	message: str,
	family_spec: Dict[str, Any],
	ranking_limit: int,
	sort_direction: str,
) -> Dict[str, Any]:
	as_of_date = _extract_as_of_date_scope(message)
	if not as_of_date and _clean_text(family_spec.get("default_as_of_date_policy")) == "current_governed_report_date":
		as_of_date = current_date_iso()
	if not as_of_date:
		return {
			"ranking_limit": ranking_limit,
			"sort_direction": sort_direction,
		}
	return {
		"requested_time_scope": "as_of_date",
		"as_of_date": as_of_date,
		"has_as_of_date": True,
		"ranking_limit": ranking_limit,
		"sort_direction": sort_direction,
	}


def _period_requested_scope(requested_time_scope: str, ranking_limit: int, sort_direction: str) -> Dict[str, Any]:
	start_date, end_date = _date_range_from_time_scope(requested_time_scope)
	if not start_date or not end_date:
		return {
			"ranking_limit": ranking_limit,
			"sort_direction": sort_direction,
		}
	return {
		"requested_time_scope": requested_time_scope,
		"period_start": start_date,
		"period_end": end_date,
		"has_period_scope": True,
		"ranking_limit": ranking_limit,
		"sort_direction": sort_direction,
	}


def _time_scope_from_period(period_start: str, period_end: str) -> str:
	start = _clean_text(period_start)
	end = _clean_text(period_end)
	if not start or not end:
		return ""
	for candidate in _PERIOD_SCOPE_ORDER:
		candidate_start, candidate_end = _date_range_from_time_scope(candidate)
		if candidate_start == start and candidate_end == end:
			return candidate
	return ""


def _title_case_metric(metric_id: str) -> str:
	return _clean_text(metric_id).replace("_", " ").title()


def _metric_label(metric_id: str) -> str:
	value = _clean_text(metric_id)
	if value == "revenue":
		return "Revenue"
	if value == "quantity":
		return "Quantity"
	if value == "average_order_value":
		return "Average Order Value"
	if value == "average_invoice_value":
		return "Average Invoice Value"
	if value == "average_selling_price":
		return "Average Selling Price"
	return _title_case_metric(value)


def _family_only_metric_requested(
	*,
	primary_metric: str,
	secondary_metrics: List[str],
) -> bool:
	generic_metric_ids = {"revenue", "quantity"}
	for metric_id in [_clean_text(primary_metric)] + [_clean_text(value) for value in secondary_metrics]:
		if metric_id and metric_id not in generic_metric_ids:
			return True
	return False


def _implied_basis_from_metric_ids(metric_ids: List[str]) -> str:
	implied_basis_values = {
		"average_order_value": "sales_order",
		"average_invoice_value": "sales_invoice",
	}
	resolved = {
		implied_basis_values[metric_id]
		for metric_id in [_clean_text(metric_id) for metric_id in metric_ids]
		if metric_id in implied_basis_values
	}
	if len(resolved) == 1:
		return next(iter(resolved))
	return ""


def _doc_type_to_basis(doc_type: Any) -> str:
	normalized = _clean_text(doc_type).lower().replace(" ", "_")
	if normalized in {"sales_order", "sales_orders"}:
		return "sales_order"
	if normalized in {"sales_invoice", "sales_invoices"}:
		return "sales_invoice"
	return ""


def _default_basis_from_family_spec(family_spec: Dict[str, Any]) -> str:
	if _clean_text(family_spec.get("default_basis_policy")) != "source_report_default_doc_type":
		return ""
	report_name = _clean_text(family_spec.get("default_basis_source_report"))
	if not report_name:
		return ""
	report_spec = get_report_spec(report_name)
	defaultable_filters = report_spec.get("defaultable_filters") if isinstance(report_spec, dict) else []
	if not isinstance(defaultable_filters, list):
		return ""
	for item in defaultable_filters:
		if not isinstance(item, dict):
			continue
		if _clean_text(item.get("fieldname")) != "doc_type":
			continue
		doc_type_value = item.get("value")
		resolved_basis = _doc_type_to_basis(doc_type_value)
		if resolved_basis:
			return resolved_basis
	return ""


def _primary_metric_phrase(metric_id: str) -> str:
	value = _clean_text(metric_id)
	if value == "average_order_value":
		return "average order value"
	if value == "average_invoice_value":
		return "average invoice value"
	return value.replace("_", " ")


def _secondary_metric_phrase(metric_id: str) -> str:
	return _primary_metric_phrase(metric_id)


def _basis_option_label(basis: str) -> str:
	value = _clean_text(basis)
	if value == "sales_order":
		return "Sales Order"
	if value == "sales_invoice":
		return "Sales Invoice"
	return _title_case_metric(value)


def _basis_context_phrase(basis: str) -> str:
	value = _clean_text(basis)
	if value == "sales_order":
		return "sales orders"
	if value == "sales_invoice":
		return "sales invoices"
	if value == "approved_customer_risk_as_of_default":
		return "approved customer risk metrics"
	return value.replace("_", " ")


def _basis_document_phrase(basis: str) -> str:
	value = _clean_text(basis)
	if value == "sales_order":
		return "submitted sales orders"
	if value == "sales_invoice":
		return "submitted sales invoices"
	context_phrase = _basis_context_phrase(basis)
	return context_phrase or "documents"


def _pluralize_label(label: str, count: int) -> str:
	value = _clean_text(label)
	if not value:
		return "entity" if count == 1 else "entities"
	lower_value = value.lower()
	if count == 1:
		return value
	if lower_value.endswith("y") and len(lower_value) > 1 and lower_value[-2] not in "aeiou":
		return value[:-1] + "ies"
	if lower_value.endswith(("s", "x", "z", "ch", "sh")):
		return value + "es"
	return value + "s"


def _limited_result_intro(
	*,
	period_phrase: str,
	actual_row_count: int,
	entity_label: str,
	primary_metric_id: str,
	basis: str,
	source_document_count: int = 0,
) -> str:
	verb = "was" if actual_row_count == 1 else "were"
	pronoun = "it is" if actual_row_count == 1 else "they are"
	entity_phrase = _pluralize_label(entity_label, actual_row_count)
	basis_context = _basis_context_phrase(basis)
	document_phrase = _basis_document_phrase(basis)
	if source_document_count > actual_row_count:
		return (
			f"For {period_phrase}, there {verb} {source_document_count} {document_phrase} "
			f"from {actual_row_count} {entity_phrase} in that period, so here {pronoun} ranked by {_primary_metric_phrase(primary_metric_id)}."
		)
	if basis_context:
		return (
			f"For {period_phrase}, there {verb} only {actual_row_count} {entity_phrase} "
			f"with {basis_context} in that period, so here {pronoun} ranked by {_primary_metric_phrase(primary_metric_id)}."
		)
	return (
		f"For {period_phrase}, there {verb} only {actual_row_count} {entity_phrase} "
		f"in that period, so here {pronoun} ranked by {_primary_metric_phrase(primary_metric_id)}."
	)


def _source_report_names(source_refs: List[Dict[str, Any]]) -> List[str]:
	out: List[str] = []
	for source_ref in source_refs or []:
		if not isinstance(source_ref, dict):
			continue
		for report_name in (source_ref.get("report_names") or []):
			if isinstance(report_name, dict):
				clean_report_name = _clean_text(report_name.get("report_name"))
			else:
				clean_report_name = _clean_text(report_name)
			if clean_report_name and clean_report_name not in out:
				out.append(clean_report_name)
	return out


def _followup_column_alias_map(
	*,
	family_spec: Dict[str, Any],
	metric_ids: List[str],
) -> Dict[str, str]:
	alias_map: Dict[str, str] = {
		"entity": "entity",
		"entity_name": "entity",
		"product": "entity",
		"product_name": "entity",
		"item": "entity",
		"item_name": "entity",
		"customer": "entity",
		"customer_name": "entity",
		"name": "entity",
		"code": "entity_code",
		"item_code": "entity_code",
		"product_code": "entity_code",
	}
	if _clean_text(family_spec.get("entity_grain")) == "customer":
		alias_map["party_name"] = "entity"
	subject_alias = _clean_text(family_spec.get("subject_alias_value"))
	if subject_alias:
		for variant in _alias_variants(subject_alias):
			alias_map[variant] = "entity"
	metric_map = dict(family_spec.get("metric_semantic_key_map") or {})

	def _register_aliases(target_metric_id: str, *alias_values: str) -> None:
		for alias_value in alias_values:
			for variant in _alias_variants(alias_value):
				alias_map[variant] = target_metric_id

	for metric_id in [_clean_text(value) for value in (metric_ids or []) if _clean_text(value)]:
		_register_aliases(metric_id, metric_id, _metric_label(metric_id))
		for semantic_key in [
			_clean_text(value)
			for value in (metric_map.get(metric_id) or [])
			if _clean_text(value)
		]:
			_register_aliases(metric_id, semantic_key, _metric_label(semantic_key))
			for alias in get_aliases(semantic_key):
				_register_aliases(metric_id, alias)
		for row_key in _metric_row_keys(metric_id):
			_register_aliases(metric_id, row_key, _metric_label(row_key))
			for alias in get_aliases(row_key):
				_register_aliases(metric_id, alias)
	return alias_map


def _metric_row_keys(metric_id: str) -> List[str]:
	value = _clean_text(metric_id)
	if value == "revenue":
		return ["revenue", "sales_amount"]
	if value == "average_selling_price":
		return ["average_selling_price"]
	return [value] if value else []


def _row_evidence_sections(row: Dict[str, Any]) -> Dict[str, Any]:
	out: Dict[str, Any] = {}
	for key in ("aging_buckets",):
		value = row.get(key)
		if isinstance(value, list):
			rows = [dict(item) for item in value if isinstance(item, dict)]
			if rows:
				out[key] = rows
	return out


def _normalized_ranked_rows_from_composite(composite_artifact_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	rows = [dict(item) for item in (composite_artifact_payload.get("rows") or []) if isinstance(item, dict)]
	out: List[Dict[str, Any]] = []
	for row in rows:
		entity_name = _clean_text(
			row.get("entity_name")
			or row.get("item_name")
			or row.get("customer_name")
			or row.get("entity")
			or row.get("item_code")
			or row.get("customer")
		)
		if not entity_name:
			continue
		entity_code = _clean_text(row.get("entity_code") or row.get("item_code") or row.get("customer"))
		normalized_row: Dict[str, Any] = {
			"rank": int(row.get("rank") or len(out) + 1),
			"entity": entity_name,
			"entity_name": entity_name,
			"entity_code": entity_code,
			"customer": _clean_text(row.get("customer") or entity_code or entity_name),
			"customer_name": _clean_text(row.get("customer_name") or entity_name),
			"item": _clean_text(row.get("item") or entity_name),
			"item_name": _clean_text(row.get("item_name") or entity_name),
			"item_code": _clean_text(row.get("item_code") or entity_code),
		}
		metric_values = dict(row.get("metric_values") or {})
		for metric_id, metric_payload in metric_values.items():
			if not isinstance(metric_payload, dict):
				continue
			for row_key in _metric_row_keys(metric_id):
				normalized_row[row_key] = metric_payload.get("value")
		normalized_row.update(_row_evidence_sections(row))
		out.append(normalized_row)
	return out


def _normalized_summary_rows(
	*,
	rows: List[Dict[str, Any]],
	primary_metric_id: str,
) -> List[Dict[str, Any]]:
	if not rows:
		return []
	primary_metric_key = _metric_row_keys(primary_metric_id)[0] if _metric_row_keys(primary_metric_id) else primary_metric_id
	total_value = sum(float(row.get(primary_metric_key) or 0.0) for row in rows)
	top_row = dict(rows[0] or {})
	top_entity = _clean_text(top_row.get("entity_name") or top_row.get("entity"))
	top_value = float(top_row.get(primary_metric_key) or 0.0)
	return [
		{"label": f"Total {_metric_label(primary_metric_id)}", "metric_key": primary_metric_key, "amount": total_value},
		{"label": "Top Entity", "metric_key": "top_entity", "value": top_entity},
		{"label": f"Top {_metric_label(primary_metric_id)}", "metric_key": "top_value", "amount": top_value},
	]


def _build_followup_ready_family_artifact(
	*,
	request_id: str,
	raw_message: str,
	family_spec: Dict[str, Any],
	family_resolution: CompositeFamilyResolutionContract,
	composite_artifact_payload: Dict[str, Any],
	source_reports: List[str],
) -> Dict[str, Any]:
	local_followup_family_id = _clean_text(family_spec.get("local_followup_family_id"))
	if not local_followup_family_id:
		return {}
	primary_metric_id = _clean_text(composite_artifact_payload.get("primary_metric_id"))
	secondary_metric_ids = [
		_clean_text(value)
		for value in (composite_artifact_payload.get("secondary_metric_ids") or [])
		if _clean_text(value)
	]
	display_secondary_metric_ids = _display_secondary_metric_ids(
		primary_metric_id=primary_metric_id,
		requested_secondary_metric_ids=list(family_resolution.requested_secondary_metrics or []),
		available_secondary_metric_ids=secondary_metric_ids,
	)
	ranked_rows = _normalized_ranked_rows_from_composite(composite_artifact_payload)
	if not ranked_rows or not primary_metric_id:
		return {}
	entity_grain = _clean_text(family_spec.get("entity_grain") or composite_artifact_payload.get("entity_grain"))
	entity_dimension = composite_entity_dimension_label(entity_grain)
	available_metric_keys = list(
		dict.fromkeys(
			[
				*[_clean_text(value) for value in [primary_metric_id, *secondary_metric_ids] if _clean_text(value)],
				*[
					row_key
					for metric_id in [primary_metric_id, *secondary_metric_ids]
					for row_key in _metric_row_keys(metric_id)
					if _clean_text(row_key)
				],
			]
		)
	)
	requested_columns = ["entity", primary_metric_id, *display_secondary_metric_ids]
	composite_time_scope = _time_scope_from_period(
		family_resolution.requested_period_start,
		family_resolution.requested_period_end,
	)
	as_of_date = _clean_text(family_resolution.requested_as_of_date)
	entity_column_alias_map = _followup_column_alias_map(
		family_spec=family_spec,
		metric_ids=[primary_metric_id, *secondary_metric_ids],
	)
	dimensions = apply_analytical_scope_runtime_policy(
		family_id=local_followup_family_id,
		report_name=source_reports[0] if source_reports else _clean_text(family_resolution.family_label),
		dimensions={
			"entity_dimension": entity_dimension,
			"primary_metric_key": primary_metric_id,
			"primary_metric_label": _metric_label(primary_metric_id),
			"requested_metric_key": primary_metric_id,
			"requested_columns": requested_columns,
			"requested_projection_mode": (
				"explicit_selection" if display_secondary_metric_ids else "default"
			),
			"available_metric_keys": available_metric_keys,
			"requested_top_n": int(max(1, family_resolution.requested_limit or len(ranked_rows) or 10)),
			"requested_sort_direction": family_resolution.requested_sort_direction or "desc",
			"source_grain": "entity_total",
			"requested_column_alias_map": entity_column_alias_map,
			"source_composite_family_id": _clean_text(family_resolution.family_id),
			"source_composite_family_label": _clean_text(family_resolution.family_label),
			"source_composite_subject_alias": _clean_text(family_spec.get("subject_alias_value")),
			"source_composite_basis": _clean_text(family_resolution.requested_basis),
			"source_composite_primary_metric_id": primary_metric_id,
			"source_composite_secondary_metric_ids": list(display_secondary_metric_ids),
			"source_composite_time_scope": composite_time_scope,
			"source_composite_as_of_date": as_of_date,
			"source_composite_followup_affordances": [
				_clean_text(value)
				for value in (family_spec.get("followup_affordances") or [])
				if _clean_text(value)
			],
			"source_composite_id": _clean_text(composite_artifact_payload.get("composite_id")),
		},
	)
	artifact_contract = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id=local_followup_family_id,
		source_reports=source_reports,
		period={
			"from_date": family_resolution.requested_period_start,
			"to_date": family_resolution.requested_period_end,
			"as_of_date": as_of_date,
			"report_date": as_of_date,
			"time_scope": composite_time_scope,
			"requested_time_scope": composite_time_scope,
		},
			filters={
				"company": family_resolution.requested_company_name,
				"basis": family_resolution.requested_basis,
				"as_of_date": as_of_date,
				"composite_family_id": _clean_text(family_resolution.family_id),
			},
			dimensions=dimensions,
		metrics={
			primary_metric_id: sum(float(row.get(_metric_row_keys(primary_metric_id)[0]) or 0.0) for row in ranked_rows),
			"entity_count": len(ranked_rows),
			"top_value": float(ranked_rows[0].get(_metric_row_keys(primary_metric_id)[0]) or 0.0),
			"as_of_date": as_of_date,
		},
		sections={
			"ranked_rows": ranked_rows,
			"summary": _normalized_summary_rows(rows=ranked_rows, primary_metric_id=primary_metric_id),
		},
	)
	return artifact_contract.to_payload()


def _build_followup_ready_rendered_response(
	*,
	request_id: str,
	normalized_family_artifact_payload: Dict[str, Any],
) -> Dict[str, Any]:
	if not normalized_family_artifact_payload:
		return {}
	artifact_contract = build_normalized_family_artifact_contract(
		request_id=_clean_text(normalized_family_artifact_payload.get("request_id") or request_id),
		family_id=_clean_text(normalized_family_artifact_payload.get("family_id")),
		artifact_type=_clean_text(normalized_family_artifact_payload.get("artifact_type") or "normalized_family_artifact"),
		source_reports=list(normalized_family_artifact_payload.get("source_reports") or []),
		period=dict(normalized_family_artifact_payload.get("period") or {}),
		filters=dict(normalized_family_artifact_payload.get("filters") or {}),
		dimensions=dict(normalized_family_artifact_payload.get("dimensions") or {}),
		metrics=dict(normalized_family_artifact_payload.get("metrics") or {}),
		sections=dict(normalized_family_artifact_payload.get("sections") or {}),
		warnings=list(normalized_family_artifact_payload.get("warnings") or []),
	)
	render_outcome = render_normalized_family_response(
		request_id=request_id,
		artifact_contract=artifact_contract,
		response_overrides=None,
	)
	if render_outcome.contract is None:
		return {}
	return render_outcome.contract.to_payload()


def _build_followup_ready_grounded_turn_context(
	*,
	request_id: str,
	raw_message: str,
	resolved_company_name: str,
	family_resolution: CompositeFamilyResolutionContract,
	normalized_family_artifact_payload: Dict[str, Any],
	source_reports: List[str],
) -> Dict[str, Any]:
	if not normalized_family_artifact_payload:
		return {}
	dimensions = dict(normalized_family_artifact_payload.get("dimensions") or {})
	sections = dict(normalized_family_artifact_payload.get("sections") or {})
	rows = [dict(item) for item in (sections.get("ranked_rows") or []) if isinstance(item, dict)]
	entity_dimension = _clean_text(dimensions.get("entity_dimension")) or "Entity"
	entity_type = normalize_item_product_grain(entity_dimension)
	known_entities = [
		{
			"entity_type": entity_type,
			"name": _clean_text(row.get("entity_name") or row.get("entity")),
			"code": _clean_text(row.get("entity_code") or row.get("item_code") or row.get("customer")),
			"rank": int(row.get("rank") or 0),
			"source_family_id": _clean_text(dimensions.get("source_composite_family_id")),
		}
		for row in rows[:25]
		if _clean_text(row.get("entity_name") or row.get("entity"))
	]
	as_of_date = _clean_text(
		getattr(family_resolution, "requested_as_of_date", "")
		or (normalized_family_artifact_payload.get("period") or {}).get("as_of_date")
		or (normalized_family_artifact_payload.get("period") or {}).get("report_date")
	)
	grounded_turn = GroundedTurnContext(
		request_id=request_id,
		trace_request_id=request_id,
		grounded=True,
		source_kind="frontdoor_composite",
		source_name=_clean_text(normalized_family_artifact_payload.get("family_id") or "ranking_analytics"),
		company=resolved_company_name,
		date_range={
			"from_date": family_resolution.requested_period_start,
			"to_date": family_resolution.requested_period_end,
			"as_of_date": as_of_date,
			"report_date": as_of_date,
		},
			filters={
				"company": resolved_company_name,
				"basis": family_resolution.requested_basis,
				"as_of_date": as_of_date,
				"composite_family_id": _clean_text(getattr(family_resolution, "family_id", "")),
			},
			dimensions=[entity_dimension],
			metrics=[
				_clean_text(value)
				for value in (dimensions.get("available_metric_keys") or [])
				if _clean_text(value)
			],
			returned_schema=[entity_dimension, *[_metric_label(value) for value in (dimensions.get("requested_columns") or [])[1:]]],
		table_rows=rows[:100],
		row_count=len(rows),
		base_language=detect_language(raw_message),
		transform_chain=[],
		artifact_family_id=_clean_text(normalized_family_artifact_payload.get("family_id")),
		artifact_type=_clean_text(normalized_family_artifact_payload.get("artifact_type")),
		artifact_source_reports=source_reports,
		known_entities=known_entities,
		known_documents=[],
	)
	return grounded_turn.to_payload()


def _build_followup_ready_runtime_trace(
	*,
	request_id: str,
	family_resolution: CompositeFamilyResolutionContract,
	composite_artifact_payload: Dict[str, Any],
) -> Dict[str, Any]:
	composite_id = _clean_text(composite_artifact_payload.get("composite_id"))
	return tool_trace_payload(
		request_id=request_id,
		ok=True,
		tool_trace=[
			{
				"tool": "frontdoor-governed-composite-runtime",
				"status": "ok",
				"detail": composite_id,
				"detail_obj": {
					"family_id": family_resolution.family_id,
					"composite_id": composite_id,
					"basis": family_resolution.requested_basis,
					"period_start": family_resolution.requested_period_start,
					"period_end": family_resolution.requested_period_end,
				},
			}
		],
		agent_meta={
			"engine": "frontdoor_governed_composite_runtime",
			"family_id": family_resolution.family_id,
			"composite_id": composite_id,
		},
		error="",
		runtime_latency_ms=0,
	)


def _period_scope_label(canonical_scope: str) -> str:
	labels = {
		"last_month": "Last Month",
		"current_fiscal_year_to_date": "Current Fiscal Year to Date",
		"last_year": "Last Year",
	}
	return labels.get(_clean_text(canonical_scope), _title_case_metric(canonical_scope))


def _composite_continuation_message(
	*,
	family_spec: Dict[str, Any],
	primary_metric_id: str,
	secondary_metric_ids: List[str],
	basis: str,
	time_scope: str,
	limit: int,
) -> str:
	subject = _clean_text(family_spec.get("subject_alias_value")) or "items"
	limit_phrase = f"top {limit}" if int(limit or 0) > 0 else "top"
	base = f"show {limit_phrase} {subject}s by {_primary_metric_phrase(primary_metric_id)}".strip()
	if basis:
		base = f"{base} for {_basis_context_phrase(basis)}"
	if time_scope:
		if time_scope == "last_month":
			base = f"{base} last month"
		elif time_scope == "current_fiscal_year_to_date":
			base = f"{base} current fiscal year to date"
		elif time_scope == "last_year":
			base = f"{base} last year"
		else:
			base = f"{base} {_clean_text(time_scope)}"
	if secondary_metric_ids:
		base = f"{base} with {' and '.join(_secondary_metric_phrase(metric_id) for metric_id in secondary_metric_ids)}"
	return base.strip()


def _clarification_axis(family_resolution: CompositeFamilyResolutionContract) -> str:
	missing = list(family_resolution.missing_clarifications or [])
	for axis in _CLARIFICATION_PRIORITY:
		if axis in missing:
			return axis
	return missing[0] if missing else ""


def _clarification_options_for_axis(family_spec: Dict[str, Any], axis: str) -> List[str]:
	supported_values = dict(family_spec.get("supported_variation_values") or {})
	if axis == "primary_sort_metric":
		return [_title_case_metric(value) for value in supported_values.get("primary_sort_metric") or []]
	if axis == "basis":
		return [_basis_option_label(value) for value in supported_values.get("basis") or []]
	if axis == "scope":
		return [_period_scope_label(value) for value in _PERIOD_SCOPE_ORDER]
	return []


def _option_aliases_for_axis(family_spec: Dict[str, Any], axis: str, option_label: str) -> List[str]:
	if axis == "basis":
		if option_label == "Sales Order":
			return ["sales order", "sales orders"]
		if option_label == "Sales Invoice":
			return ["sales invoice", "sales invoices"]
	if axis == "primary_sort_metric":
		option_value = _option_value_for_axis(family_spec, axis, option_label)
		metric_map = dict(family_spec.get("metric_semantic_key_map") or {})
		semantic_keys = [
			_clean_text(value)
			for value in (metric_map.get(option_value) or [])
			if _clean_text(value)
		]
		aliases: List[str] = []
		for semantic_key in semantic_keys:
			for alias in get_aliases(semantic_key):
				clean_alias = _clean_text(alias).lower()
				if clean_alias and clean_alias not in aliases:
					aliases.append(clean_alias)
		if aliases:
			return aliases
	if axis == "scope":
		return [_clean_text(option_label).lower()]
	return [_clean_text(option_label).lower()]


def _option_value_for_axis(family_spec: Dict[str, Any], axis: str, option_label: str) -> str:
	supported_values = dict(family_spec.get("supported_variation_values") or {})
	if axis == "primary_sort_metric":
		for value in supported_values.get("primary_sort_metric") or []:
			if _title_case_metric(value) == option_label:
				return _clean_text(value)
	if axis == "basis":
		for value in supported_values.get("basis") or []:
			if _basis_option_label(value) == option_label:
				return _clean_text(value)
	if axis == "scope":
		for value in _PERIOD_SCOPE_ORDER:
			if _period_scope_label(value) == option_label:
				return value
	return ""


def _requested_time_scope_from_family_resolution(family_resolution: CompositeFamilyResolutionContract) -> str:
	if family_resolution.requested_period_start and family_resolution.requested_period_end:
		for candidate in _PERIOD_SCOPE_ORDER:
			start_date, end_date = _date_range_from_time_scope(candidate)
			if start_date == family_resolution.requested_period_start and end_date == family_resolution.requested_period_end:
				return candidate
	return ""


def _clarification_semantic_slot_name(axis: str) -> str:
	if axis == "primary_sort_metric":
		return "requested_primary_metric"
	if axis == "basis":
		return "requested_basis"
	if axis == "scope":
		return "selected_time_scope"
	return ""


def _clarification_carryover_slot_values(
	*,
	family_spec: Dict[str, Any],
	family_resolution: CompositeFamilyResolutionContract,
	axis: str,
) -> Dict[str, str]:
	requested_time_scope = _requested_time_scope_from_family_resolution(family_resolution)
	values = {
		"family_id": family_resolution.family_id or _clean_text(family_spec.get("family_id")),
		"requested_limit": str(int(family_resolution.requested_limit or 0)) if int(family_resolution.requested_limit or 0) > 0 else "",
		"requested_sort_direction": _clean_text(family_resolution.requested_sort_direction),
	}
	if axis != "primary_sort_metric" and family_resolution.requested_primary_metric:
		values["requested_primary_metric"] = _clean_text(family_resolution.requested_primary_metric)
	if axis != "basis" and family_resolution.requested_basis:
		values["requested_basis"] = _clean_text(family_resolution.requested_basis)
	if axis != "scope" and requested_time_scope:
		values["selected_time_scope"] = requested_time_scope
	return {
		key: value
		for key, value in values.items()
		if _clean_text(key) and _clean_text(value)
	}


def _clarification_answer(
	*,
	family_spec: Dict[str, Any],
	family_resolution: CompositeFamilyResolutionContract,
	axis: str,
	options: List[str],
) -> str:
	period_start = _clean_text(family_resolution.requested_period_start)
	period_end = _clean_text(family_resolution.requested_period_end)
	subject_label = _clean_text(family_spec.get("subject_alias_value"))
	subject_label_plural = f"{subject_label}s" if subject_label else "entities"
	if axis == "primary_sort_metric":
		if period_start and period_end:
			return render_shared_choice_list_clarification(
				reason_type="composite_family_variation",
				variant="primary_sort_metric_with_period",
				template_values={
					"subject_label_plural": subject_label_plural,
					"period_start": period_start,
					"period_end": period_end,
				},
				options=options,
				default_question=(
					f"I can rank {subject_label_plural} for "
					f"{period_start} to {period_end}, but I still need the primary metric."
				),
			)
		return render_shared_choice_list_clarification(
			reason_type="composite_family_variation",
			variant="primary_sort_metric_default",
			template_values={
				"subject_label_plural": subject_label_plural,
			},
			options=options,
			default_question=f"I can rank {subject_label_plural}, but I still need the primary metric.",
		)
	if axis == "basis":
		primary_metric_phrase = _primary_metric_phrase(family_resolution.requested_primary_metric)
		return render_shared_choice_list_clarification(
			reason_type="composite_family_variation",
			variant="basis",
			template_values={
				"subject_label_plural": subject_label_plural,
				"primary_metric_phrase": primary_metric_phrase,
			},
			options=options,
			default_question=(
				f"I can rank {subject_label_plural} by "
				f"{primary_metric_phrase}, but I still need the approved basis."
			),
		)
	basis_suffix = (
		f" for {_basis_context_phrase(family_resolution.requested_basis)}"
		if family_resolution.requested_basis
		else ""
	)
	primary_metric_phrase = _primary_metric_phrase(family_resolution.requested_primary_metric)
	return render_shared_choice_list_clarification(
		reason_type="composite_family_variation",
		variant="scope",
		template_values={
			"subject_label_plural": subject_label_plural,
			"primary_metric_phrase": primary_metric_phrase,
			"basis_suffix": basis_suffix,
		},
		options=options,
		default_question=(
			f"I can rank {subject_label_plural} by "
			f"{primary_metric_phrase}{basis_suffix}, but I still need the business period."
		),
	)


def _build_family_clarification_signal(
	*,
	request_id: str,
	family_spec: Dict[str, Any],
	family_resolution: CompositeFamilyResolutionContract,
	answer_text: str,
	axis: str,
	options: List[str],
) -> Dict[str, Any]:
	resolved_message_by_option: Dict[str, str] = {}
	option_aliases_by_option: Dict[str, List[str]] = {}
	semantic_slot_value_by_option: Dict[str, str] = {}
	for option in options:
		value = _option_value_for_axis(family_spec, axis, option)
		primary_metric = family_resolution.requested_primary_metric
		basis = family_resolution.requested_basis
		time_scope = _requested_time_scope_from_family_resolution(family_resolution)
		if axis == "primary_sort_metric":
			primary_metric = value
		elif axis == "basis":
			basis = value
		elif axis == "scope":
			time_scope = value
		resolved_message_by_option[option] = _composite_continuation_message(
			family_spec=family_spec,
			primary_metric_id=primary_metric,
			secondary_metric_ids=list(family_resolution.requested_secondary_metrics or []),
			basis=basis,
			time_scope=time_scope,
			limit=int(family_resolution.requested_limit or 10),
		)
		option_aliases_by_option[option] = _option_aliases_for_axis(family_spec, axis, option)
		if value:
			semantic_slot_value_by_option[option] = value
	semantic_slot_name = _clarification_semantic_slot_name(axis)
	carryover_slot_values = _clarification_carryover_slot_values(
		family_spec=family_spec,
		family_resolution=family_resolution,
		axis=axis,
	)
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="frontdoor",
		reason_type="composite_family_variation",
		user_question=answer_text,
		suggested_options=options,
		internal_reason="The governed composite family request needs one more approved variation before execution can proceed.",
		internal_details={
			"continuation_lane": "front_door",
			"continuation_intent_class": "governed_composite_value",
			"clarification_template_group": "shared_clarification",
			"resolved_message_by_option": resolved_message_by_option,
			"option_aliases_by_option": option_aliases_by_option,
			"semantic_slot_name": semantic_slot_name if semantic_slot_value_by_option else "",
			"semantic_slot_value_by_option": semantic_slot_value_by_option,
			"carryover_slot_values": carryover_slot_values,
			"family_id": family_resolution.family_id or _clean_text(family_spec.get("family_id")),
			"clarification_axis": axis,
		},
	).to_payload()


def _component_metric_id(execution_spec: Dict[str, Any]) -> str:
	return _clean_text(dict(execution_spec.get("value_metric_mapping") or {}).get("family_metric_id"))


def _select_secondary_metric_ids(
	artifact_spec: Dict[str, Any],
	primary_metric_id: str,
	requested_secondary_metric_ids: List[str],
) -> List[str]:
	requested = [_clean_text(value) for value in requested_secondary_metric_ids if _clean_text(value) and _clean_text(value) != _clean_text(primary_metric_id)]
	if requested:
		return requested
	by_primary = artifact_spec.get("default_secondary_metric_ids_by_primary_metric")
	if isinstance(by_primary, dict):
		values = [_clean_text(value) for value in (by_primary.get(primary_metric_id) or []) if _clean_text(value)]
		if values:
			return [value for value in values if value != _clean_text(primary_metric_id)]
	return [
		_clean_text(value)
		for value in (artifact_spec.get("secondary_metric_ids") or [])
		if _clean_text(value) and _clean_text(value) != _clean_text(primary_metric_id)
	]


def _display_secondary_metric_ids(
	*,
	primary_metric_id: str,
	requested_secondary_metric_ids: List[str],
	available_secondary_metric_ids: List[str],
) -> List[str]:
	requested = [
		_clean_text(value)
		for value in (requested_secondary_metric_ids or [])
		if _clean_text(value) and _clean_text(value) != _clean_text(primary_metric_id)
	]
	allowed = {
		_clean_text(value)
		for value in (available_secondary_metric_ids or [])
		if _clean_text(value)
	}
	if not requested:
		return []
	return [value for value in requested if value in allowed]


def _execute_component_ranking_artifacts(
	*,
	composite_resolution: CompositeArtifactResolutionContract,
	family_resolution: CompositeFamilyResolutionContract,
) -> Tuple[Dict[str, GovernedKpiRankingArtifactContract], List[Dict[str, Any]], str]:
	from ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution import (
		execute_governed_kpi_artifact_from_states,
	)

	component_artifacts: Dict[str, GovernedKpiRankingArtifactContract] = {}
	source_refs: List[Dict[str, Any]] = []
	for execution_id in composite_resolution.required_execution_ids:
		execution_spec = get_governed_kpi_execution_spec(execution_id)
		if not execution_spec:
			return {}, [], f"Composite references missing governed KPI execution '{execution_id}'."
		definition_id = _clean_text(execution_spec.get("definition_id"))
		formula_id = _clean_text(execution_spec.get("formula_id"))
		definition_state = resolve_business_definition_state(
			definition_id,
			lookup_mode="definition_id",
			company_name=family_resolution.requested_company_name,
		)
		formula_state = resolve_governed_formula_state(
			definition_state=definition_state,
			formula_lookup_value=formula_id,
			lookup_mode="formula_id",
			company_name=family_resolution.requested_company_name,
		)
		requested_scope = {
			"period_start": family_resolution.requested_period_start,
			"period_end": family_resolution.requested_period_end,
			"as_of_date": family_resolution.requested_as_of_date,
			"ranking_limit": 0,
			"sort_direction": family_resolution.requested_sort_direction or "desc",
		}
		execution_state = resolve_governed_kpi_execution_state(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_shape=_clean_text(execution_spec.get("execution_shape")),
			company_name=family_resolution.requested_company_name,
			requested_scope=requested_scope,
		)
		execution_payload = execute_governed_kpi_artifact_from_states(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_state=execution_state,
			requested_scope=requested_scope,
			message="",
		)
		ranking_artifact = execution_payload.get("ranking_artifact")
		if not isinstance(ranking_artifact, GovernedKpiRankingArtifactContract) or ranking_artifact.status != "active_value":
			return {}, [], f"Component execution '{execution_id}' did not produce an active governed ranking artifact."
		component_metric_id = _component_metric_id(execution_spec)
		if not component_metric_id:
			return {}, [], f"Component execution '{execution_id}' is missing family_metric_id metadata."
		component_artifacts[component_metric_id] = ranking_artifact
		source_refs.append(
			{
				"execution_id": execution_id,
				"definition_id": definition_id,
				"formula_id": formula_id,
				"report_names": list(ranking_artifact.source_evidence or []),
				"metric_id": component_metric_id,
			}
		)
	return component_artifacts, source_refs, ""


def _evaluate_composite_compatibility(
	*,
	composite_resolution: CompositeArtifactResolutionContract,
	component_artifacts: Dict[str, GovernedKpiRankingArtifactContract],
) -> Tuple[str, str]:
	for rule_id in composite_resolution.compatibility_rule_ids:
		rule_spec = get_composite_compatibility_spec(rule_id)
		if not rule_spec:
			return "blocked_missing_component", f"Composite compatibility rule '{rule_id}' is missing."
		entity_grains = {
			_clean_text(artifact.entity_grain)
			for artifact in component_artifacts.values()
			if _clean_text(artifact.entity_grain)
		}
		time_scope_types = {
			"period_required" if _clean_text(artifact.period_start) and _clean_text(artifact.period_end) else "as_of_date_required"
			for artifact in component_artifacts.values()
		}
		periods = {
			(_clean_text(artifact.period_start), _clean_text(artifact.period_end))
			for artifact in component_artifacts.values()
		}
		scopes = {
			_clean_text((artifact.scope or {}).get("company"))
			for artifact in component_artifacts.values()
		}
		allowed_entity_grain = _clean_text(rule_spec.get("allowed_entity_grain"))
		if allowed_entity_grain and entity_grains not in ({allowed_entity_grain}, set()):
			return "blocked_incompatible_grain", "Composite component entity grains are not compatible with the governed rule."
		allowed_time_scope_type = _clean_text(rule_spec.get("allowed_time_scope_type"))
		if allowed_time_scope_type and time_scope_types not in ({allowed_time_scope_type}, set()):
			return "blocked_incompatible_time_scope", "Composite component time scopes are not compatible with the governed rule."
		if bool(rule_spec.get("required_period_alignment")) and len(periods) > 1:
			return "blocked_incompatible_time_scope", "Composite component periods are not aligned."
		if bool(rule_spec.get("required_scope_alignment")) and len(scopes) > 1:
			return "blocked_incompatible_grain", "Composite component scopes are not aligned."
	return "compatible", ""


def _format_derived_metric_value(value: Any, derived_spec: Dict[str, Any]) -> str:
	format_style = _clean_text(derived_spec.get("display_format"))
	if format_style == "money_mmk":
		return f"{_money(value)} MMK"
	if format_style == "percent":
		try:
			numeric = float(value or 0.0)
		except Exception:
			numeric = 0.0
		return f"{numeric:,.1f}".rstrip("0").rstrip(".") + "%"
	if format_style == "count":
		return _count_text(value)
	return _clean_text(value)


def _assemble_entity_period_commercial_rows(
	*,
	assembly_contract: CompositeAssemblyAdapterContract,
	component_artifacts: Dict[str, GovernedKpiRankingArtifactContract],
	primary_metric_id: str,
	secondary_metric_ids: List[str],
	requested_limit: int,
	sort_direction: str,
	derived_metric_specs: Dict[str, Any] | None = None,
) -> Tuple[List[Dict[str, Any]], str]:
	primary_artifact = component_artifacts.get(primary_metric_id)
	if primary_artifact is None:
		return [], f"Primary metric '{primary_metric_id}' is missing from the governed component artifact set."
	join_key_schema = [_clean_text(value) for value in (assembly_contract.join_key_schema or []) if _clean_text(value)]
	if not join_key_schema:
		return [], "Composite assembly is missing a governed join key schema."
	component_row_maps: Dict[str, Dict[str, Dict[str, Any]]] = {}
	for metric_id, artifact in component_artifacts.items():
		row_map: Dict[str, Dict[str, Any]] = {}
		for row in artifact.rows:
			join_key = composite_row_join_key_tuple(dict(row), join_key_schema)
			if all(join_key):
				row_map["||".join(join_key)] = dict(row)
		component_row_maps[metric_id] = row_map
	primary_rows = [dict(row) for row in primary_artifact.rows if isinstance(row, dict)]
	reverse = _clean_text(sort_direction or "desc") != "asc"
	primary_rows = sorted(primary_rows, key=lambda row: float(row.get("value") or 0.0), reverse=reverse)
	if requested_limit > 0:
		primary_rows = primary_rows[:requested_limit]
	if _clean_text(assembly_contract.row_missing_component_policy) == "block_family":
		for row in primary_rows:
			join_key = "||".join(composite_row_join_key_tuple(row, join_key_schema))
			for metric_id in secondary_metric_ids:
				if join_key and join_key not in component_row_maps.get(metric_id, {}):
					return [], f"Composite row assembly is missing supporting metric '{metric_id}' for join key '{join_key}'."
	assembled_rows: List[Dict[str, Any]] = []
	for index, row in enumerate(primary_rows, start=1):
		join_key_tuple = composite_row_join_key_tuple(row, join_key_schema)
		join_key = "||".join(join_key_tuple)
		entity_name = composite_row_identity_value(row, assembly_contract.row_identity_policy)
		entity_code = composite_row_entity_code(row)
		metric_values: Dict[str, Dict[str, Any]] = {
			primary_metric_id: {
				"value": row.get("value"),
				"display_value": row.get("display_value"),
			}
		}
		row_provenance = list(row.get("row_provenance") or [])
		for metric_id in secondary_metric_ids:
			component_row = dict(component_row_maps.get(metric_id, {}).get(join_key) or {})
			if not component_row:
				derived_spec = dict((derived_metric_specs or {}).get(metric_id) or {})
				source_metric_id = _clean_text(derived_spec.get("source_metric_id")) or primary_metric_id
				value_key = _clean_text(derived_spec.get("value_key"))
				source_row = row if source_metric_id == primary_metric_id else dict(component_row_maps.get(source_metric_id, {}).get(join_key) or {})
				if source_row and value_key:
					component_row = {
						"value": source_row.get(value_key),
						"display_value": _format_derived_metric_value(source_row.get(value_key), derived_spec),
						"row_provenance": list(source_row.get("row_provenance") or []),
					}
			metric_values[metric_id] = {
				"value": component_row.get("value"),
				"display_value": component_row.get("display_value"),
			}
			row_provenance.extend(component_row.get("row_provenance") or [])
		assembled_rows.append(
			{
				"rank": index,
				"entity": entity_name,
				"entity_name": entity_name,
				"entity_code": entity_code,
				"customer": _clean_text(row.get("customer")),
				"customer_name": _clean_text(row.get("customer_name") or entity_name),
				"item": _clean_text(row.get("item") or entity_name),
				"item_code": _clean_text(row.get("item_code") or entity_code),
				"item_name": _clean_text(row.get("item_name") or entity_name),
				"metric_values": metric_values,
				"primary_metric_id": primary_metric_id,
				"row_provenance": row_provenance,
				"join_key": composite_row_join_key_payload(row, join_key_schema),
				**_row_evidence_sections(row),
			}
		)
	return assembled_rows, ""


def _render_composite_answer(
	*,
	family_resolution: CompositeFamilyResolutionContract,
	composite_artifact_payload: Dict[str, Any],
	detail_requested: bool,
) -> str:
	rows = [dict(item) for item in (composite_artifact_payload.get("rows") or []) if isinstance(item, dict)]
	if _clean_text(family_resolution.requested_as_of_date):
		period_phrase = f"as of {family_resolution.requested_as_of_date}"
	else:
		period_phrase = f"{family_resolution.requested_period_start} to {family_resolution.requested_period_end}"
	primary_metric_id = _clean_text(composite_artifact_payload.get("primary_metric_id"))
	secondary_metric_ids = [
		_clean_text(value)
		for value in (composite_artifact_payload.get("secondary_metric_ids") or [])
		if _clean_text(value)
	]
	display_secondary_metric_ids = _display_secondary_metric_ids(
		primary_metric_id=primary_metric_id,
		requested_secondary_metric_ids=list(family_resolution.requested_secondary_metrics or []),
		available_secondary_metric_ids=secondary_metric_ids,
	)
	requested_limit = int(max(1, family_resolution.requested_limit or len(rows) or 10))
	actual_row_count = len(rows)
	entity_grain = _clean_text(composite_artifact_payload.get("entity_grain") or "customer")
	entity_label = composite_entity_dimension_label(entity_grain)
	source_document_count = int(max(0, composite_artifact_payload.get("source_document_count") or 0))
	if actual_row_count and actual_row_count < requested_limit:
		intro = _limited_result_intro(
			period_phrase=period_phrase,
			actual_row_count=actual_row_count,
			entity_label=entity_label.lower(),
			primary_metric_id=primary_metric_id,
			basis=family_resolution.requested_basis,
			source_document_count=source_document_count,
		)
	else:
		prefix = "As of" if _clean_text(family_resolution.requested_as_of_date) else "For"
		basis_phrase = _basis_context_phrase(family_resolution.requested_basis)
		basis_suffix = f" based on {basis_phrase}" if basis_phrase else ""
		answer_scope = family_resolution.requested_as_of_date if prefix == "As of" else period_phrase
		intro = (
			f"{prefix} {answer_scope}, here are the top {requested_limit} "
			f"{entity_label.lower()}s by {_primary_metric_phrase(primary_metric_id)}{basis_suffix}."
		)
	answer_lines = [intro]
	if display_secondary_metric_ids:
		answer_lines.append(
			f"The table also shows {' and '.join(_secondary_metric_phrase(metric_id) for metric_id in display_secondary_metric_ids)}."
		)
	if not rows:
		answer_lines.append("No rows matched the current governed composite scope.")
	else:
		column_ids = [primary_metric_id] + list(display_secondary_metric_ids)
		header = ["Rank", entity_label] + [_title_case_metric(metric_id) for metric_id in column_ids]
		answer_lines.append("")
		answer_lines.append("| " + " | ".join(header) + " |")
		answer_lines.append("| " + " | ".join(["---"] * len(header)) + " |")
		for row in rows:
			entity_name = _clean_text(
				row.get("entity_name")
				or row.get("item_name")
				or row.get("customer_name")
				or row.get("entity")
				or row.get("item_code")
				or row.get("customer")
			)
			metric_values = dict(row.get("metric_values") or {})
			cells = [str(int(row.get("rank") or 0)), entity_name]
			for metric_id in column_ids:
				metric_payload = dict(metric_values.get(metric_id) or {})
				cells.append(_clean_text(metric_payload.get("display_value")) or "-")
			answer_lines.append("| " + " | ".join(cells) + " |")
	if detail_requested:
		answer_lines.append("")
		answer_lines.append("How it was assembled")
		answer_lines.append(f"- Basis: {_basis_context_phrase(family_resolution.requested_basis)}")
		answer_lines.append(f"- Join key: {composite_join_key_label(entity_grain)}")
		answer_lines.append("- Row assembly: left primary metric")
		answer_lines.append("- Row provenance: per-row component refs")
	return "\n".join(answer_lines).strip()


def _resolve_composite_candidate(
	*,
	message: str,
	company_name: str,
) -> Tuple[Dict[str, Any], CompositeFamilyResolutionContract | None]:
	canonical_subject = _ranking_subject(message)
	if not _has_ranking_intent(message):
		return {}, None
	requested_time_scope = _extract_period_time_scope(message)
	requested_period = _period_requested_scope(
		requested_time_scope,
		ranking_limit=_requested_top_n(message, default_limit=10),
		sort_direction=_sort_direction_from_message(message, default_direction="desc"),
	)
	candidates: List[Tuple[int, Dict[str, Any], CompositeFamilyResolutionContract]] = []
	for family_spec in list_composite_family_specs():
		if _clean_text(family_spec.get("activation_state")) != "active":
			continue
		family_subject = _clean_text(family_spec.get("subject_alias_value"))
		default_primary_requested = False
		default_trigger_requested = _family_default_trigger_requested(message, family_spec)
		if canonical_subject and canonical_subject != family_subject and not _family_subject_requested(message, family_spec):
			continue
		if not canonical_subject and not _family_subject_requested(message, family_spec) and not default_trigger_requested:
			continue
		primary_metric = _extract_primary_metric(message, family_spec)
		if not primary_metric and default_trigger_requested:
			primary_metric = _default_primary_metric_from_family_spec(family_spec)
			default_primary_requested = bool(primary_metric)
		secondary_metrics = _extract_secondary_metrics(message, family_spec, primary_metric)
		if default_primary_requested and not secondary_metrics:
			secondary_metrics = _default_secondary_metrics_from_family_spec(family_spec, primary_metric)
		explicit_basis = _extract_family_basis(message, family_spec)
		generic_metric_mix = bool(
			not explicit_basis
			and not _family_only_metric_requested(
				primary_metric=primary_metric,
				secondary_metrics=secondary_metrics,
			)
		)
		default_basis = ""
		if generic_metric_mix and secondary_metrics:
			default_basis = _default_basis_from_family_spec(family_spec)
		requested_basis = (
			explicit_basis
			or _implied_basis_from_metric_ids([primary_metric] + list(secondary_metrics))
			or default_basis
		)
		if not primary_metric and not secondary_metrics and not explicit_basis and not default_primary_requested:
			continue
		if generic_metric_mix and secondary_metrics and not default_basis:
			continue
		time_scope_type = _clean_text(family_spec.get("time_scope_type"))
		requested_scope = (
			_as_of_requested_scope(
				message,
				family_spec,
				ranking_limit=int(requested_period.get("ranking_limit") or 10),
				sort_direction=_clean_text(requested_period.get("sort_direction")),
			)
			if time_scope_type == "as_of_date_required"
			else requested_period
		)
		family_resolution = resolve_composite_family_resolution(
			requested_company_name=company_name,
			requested_family_id=_clean_text(family_spec.get("family_id")),
			requested_primary_metric=primary_metric,
			requested_secondary_metrics=secondary_metrics,
			requested_basis=requested_basis,
			requested_period_start=_clean_text(requested_scope.get("period_start")),
			requested_period_end=_clean_text(requested_scope.get("period_end")),
			requested_as_of_date=_clean_text(requested_scope.get("as_of_date")),
			requested_limit=int(requested_scope.get("ranking_limit") or 10),
			requested_sort_direction=_clean_text(requested_scope.get("sort_direction")),
		)
		if family_resolution.status not in {"resolved_family", "clarify_family_variation"}:
			continue
		priority = 2 if family_resolution.status == "resolved_family" else 1
		candidates.append((priority, dict(family_spec), family_resolution))
	if not candidates:
		return {}, None
	candidates.sort(key=lambda item: item[0], reverse=True)
	top_priority = candidates[0][0]
	best = [item for item in candidates if item[0] == top_priority]
	if len(best) != 1:
		return {}, None
	return best[0][1], best[0][2]


def governed_composite_frontdoor_candidate_available(
	*,
	message: str,
	company_name: str = "",
) -> bool:
	"""
	Return whether a message can be owned by a governed composite front-door
	family before any artifact-local follow-up lane suppresses runtime values.
	"""
	family_spec, family_resolution = _resolve_composite_candidate(
		message=message,
		company_name=_current_company_name(company_name),
	)
	return bool(
		family_spec
		and family_resolution is not None
		and family_resolution.status in {"resolved_family", "clarify_family_variation"}
	)


def maybe_build_governed_composite_frontdoor_response(
	*,
	request_id: str,
	message: str,
	company_name: str = "",
) -> Dict[str, Any]:
	raw_message = _clean_text(message)
	if not raw_message:
		return {}
	resolved_company_name = _current_company_name(company_name)
	family_spec, family_resolution = _resolve_composite_candidate(
		message=raw_message,
		company_name=resolved_company_name,
	)
	if not family_spec or family_resolution is None:
		return {}
	answer_text = ""
	clarification_signal_payload: Dict[str, Any] = {}
	composite_artifact_payload: Dict[str, Any] = {}
	normalized_family_artifact_payload: Dict[str, Any] = {}
	rendered_family_response_payload: Dict[str, Any] = {}
	grounded_turn_context_payload: Dict[str, Any] = {}
	runtime_trace_payload: Dict[str, Any] = {}
	artifact_resolution_payload: Dict[str, Any] = {}
	assembly_payload: Dict[str, Any] = {}
	if family_resolution.status == "clarify_family_variation":
		axis = _clarification_axis(family_resolution)
		options = _clarification_options_for_axis(family_spec, axis)
		if not axis or not options:
			return {}
		answer_text = _clarification_answer(
			family_spec=family_spec,
			family_resolution=family_resolution,
			axis=axis,
			options=options,
		)
		clarification_signal_payload = _build_family_clarification_signal(
			request_id=request_id,
			family_spec=family_spec,
			family_resolution=family_resolution,
			answer_text=answer_text,
			axis=axis,
			options=options,
		)
	elif family_resolution.status == "resolved_family":
		artifact_resolution = resolve_composite_artifact_resolution(
			family_resolution=family_resolution,
		)
		artifact_resolution_payload = artifact_resolution.to_payload()
		if artifact_resolution.status != "active_composite":
			return {}
		artifact_spec = get_composite_artifact_spec(artifact_resolution.composite_id)
		assembly_spec = get_composite_assembly_spec(artifact_resolution.assembly_id)
		assembly_contract = build_composite_assembly_contract_from_spec(assembly_spec)
		assembly_payload = assembly_contract.to_payload()
		component_artifacts, source_refs, component_error = _execute_component_ranking_artifacts(
			composite_resolution=artifact_resolution,
			family_resolution=family_resolution,
		)
		if component_error:
			return {}
		compatibility_status, compatibility_error = _evaluate_composite_compatibility(
			composite_resolution=artifact_resolution,
			component_artifacts=component_artifacts,
		)
		if compatibility_error:
			return {}
		primary_metric_id = family_resolution.requested_primary_metric
		secondary_metric_ids = _select_secondary_metric_ids(
			artifact_spec,
			primary_metric_id=primary_metric_id,
			requested_secondary_metric_ids=list(family_resolution.requested_secondary_metrics or []),
		)
		assembled_rows, assembly_error = _assemble_entity_period_commercial_rows(
			assembly_contract=assembly_contract,
			component_artifacts=component_artifacts,
			primary_metric_id=primary_metric_id,
			secondary_metric_ids=secondary_metric_ids,
			requested_limit=int(family_resolution.requested_limit or 10),
			sort_direction=family_resolution.requested_sort_direction or "desc",
			derived_metric_specs=dict(artifact_spec.get("derived_metric_specs") or {}),
		)
		if assembly_error:
			return {}
		composite_artifact = build_composite_governed_artifact_contract(
			composite_id=artifact_resolution.composite_id,
			label=artifact_resolution.label,
			composite_kind=artifact_resolution.composite_kind,
			primary_metric_id=primary_metric_id,
			secondary_metric_ids=secondary_metric_ids,
			entity_grain=artifact_resolution.entity_grain,
			time_scope_type=artifact_resolution.time_scope_type,
			scope={"company": family_resolution.requested_company_name},
			period_start=family_resolution.requested_period_start,
			period_end=family_resolution.requested_period_end,
			as_of_date=family_resolution.requested_as_of_date,
			row_count=len(assembled_rows),
			source_document_count=sum(
				int(max(0, (row.get("document_count") or 0)))
				for row in ((component_artifacts.get(primary_metric_id).rows) if component_artifacts.get(primary_metric_id) is not None else [])
				if isinstance(row, dict)
			),
			rows=assembled_rows,
			source_artifact_refs=source_refs,
			compatibility_status=compatibility_status,
			render_policy={"style": "business_table"},
		)
		composite_artifact_payload = composite_artifact.to_payload()
		source_reports = _source_report_names(source_refs)
		normalized_family_artifact_payload = _build_followup_ready_family_artifact(
			request_id=request_id,
			raw_message=raw_message,
			family_spec=family_spec,
			family_resolution=family_resolution,
			composite_artifact_payload=composite_artifact_payload,
			source_reports=source_reports,
		)
		rendered_family_response_payload = _build_followup_ready_rendered_response(
			request_id=request_id,
			normalized_family_artifact_payload=normalized_family_artifact_payload,
		)
		grounded_turn_context_payload = _build_followup_ready_grounded_turn_context(
			request_id=request_id,
			raw_message=raw_message,
			resolved_company_name=resolved_company_name,
			family_resolution=family_resolution,
			normalized_family_artifact_payload=normalized_family_artifact_payload,
			source_reports=source_reports,
		)
		runtime_trace_payload = _build_followup_ready_runtime_trace(
			request_id=request_id,
			family_resolution=family_resolution,
			composite_artifact_payload=composite_artifact_payload,
		)
		answer_text = _render_composite_answer(
			family_resolution=family_resolution,
			composite_artifact_payload=composite_artifact_payload,
			detail_requested=_runtime_detail_requested(raw_message),
		)
	else:
		return {}
	intent_spec = get_frontdoor_intent_spec("governed_composite_value")
	if not intent_spec:
		intent_spec = {
			"intent_class_id": "governed_composite_value",
			"response_mode": "direct_answer",
			"route_target": "front_door",
			"handle_in_front_door": True,
		}
	reason = (
		f"The turn is a governed composite family request for '{family_resolution.family_label or family_resolution.family_id}', "
		"so it should be answered from the approved composite family runtime."
	)
	semantic_result = SemanticFrontDoorResult(
		status="accepted",
		intent=SemanticFrontDoorIntent(
			intent_class="governed_composite_value",
			confidence=1.0,
			reason=reason,
		),
		confidence_threshold=1.0,
	)
	frontdoor_contract = FrontDoorIntentGateContract(
		request_id=_clean_text(request_id),
		intent_class="governed_composite_value",
		confidence=1.0,
		handle_in_front_door=bool(intent_spec.get("handle_in_front_door", True)),
		response_mode=_clean_text(intent_spec.get("response_mode") or "direct_answer") or "direct_answer",
		response_payload={
			"text": answer_text,
			"company_name": resolved_company_name,
			"family_resolution": family_resolution.to_payload(),
			"artifact_resolution": artifact_resolution_payload,
			"assembly_contract": assembly_payload,
			"composite_artifact": composite_artifact_payload,
			"normalized_family_artifact": normalized_family_artifact_payload,
			"rendered_family_response": rendered_family_response_payload,
			"grounded_turn_context": grounded_turn_context_payload,
			"runtime_trace_payload": runtime_trace_payload,
			"clarification_signal_payload": clarification_signal_payload,
		},
		route_target=_clean_text(intent_spec.get("route_target") or "front_door") or "front_door",
		reason=reason,
	)
	return {
		"semantic_result": semantic_result,
		"frontdoor_contract": frontdoor_contract,
		"frontdoor_answer": answer_text,
		"family_resolution": family_resolution.to_payload(),
		"artifact_resolution": artifact_resolution_payload,
		"assembly_contract": assembly_payload,
		"composite_artifact": composite_artifact_payload,
		"normalized_family_artifact": normalized_family_artifact_payload,
		"rendered_family_response": rendered_family_response_payload,
		"grounded_turn_context": grounded_turn_context_payload,
		"runtime_trace_payload": runtime_trace_payload,
		"clarification_signal_payload": clarification_signal_payload,
	}


def run_governed_customer_commercial_composite_probe() -> Dict[str, Any]:
	def _summary(payload: Dict[str, Any]) -> Dict[str, Any]:
		if not isinstance(payload, dict):
			return {}
		semantic_result = payload.get("semantic_result")
		frontdoor_contract = payload.get("frontdoor_contract")
		composite_artifact = payload.get("composite_artifact") if isinstance(payload.get("composite_artifact"), dict) else {}
		rows = composite_artifact.get("rows") if isinstance(composite_artifact.get("rows"), list) else []
		first_row = dict(rows[0] or {}) if rows else {}
		metric_values = first_row.get("metric_values") if isinstance(first_row.get("metric_values"), dict) else {}
		return {
			"frontdoor_answer": _clean_text(payload.get("frontdoor_answer")),
			"semantic_result": semantic_result.to_payload() if hasattr(semantic_result, "to_payload") else {},
			"frontdoor_contract": frontdoor_contract.to_payload() if hasattr(frontdoor_contract, "to_payload") else {},
			"family_resolution": dict(payload.get("family_resolution") or {}),
			"artifact_resolution": dict(payload.get("artifact_resolution") or {}),
			"assembly_contract": dict(payload.get("assembly_contract") or {}),
			"clarification_signal_payload": dict(payload.get("clarification_signal_payload") or {}),
			"composite_artifact": {
				"composite_id": _clean_text(composite_artifact.get("composite_id")),
				"row_count": len(rows),
				"first_row_entity": _clean_text(
					first_row.get("entity_name")
					or first_row.get("item_name")
					or first_row.get("customer_name")
					or first_row.get("entity")
					or first_row.get("item_code")
					or first_row.get("customer")
				),
				"first_row_metric_values": {
					metric_id: {
						"value": metric_payload.get("value"),
						"display_value": _clean_text(metric_payload.get("display_value")),
					}
					for metric_id, metric_payload in metric_values.items()
					if isinstance(metric_payload, dict)
				},
			},
		}

	company_name = "Mingalar Mobile Distribution Co., Ltd."
	active = maybe_build_governed_composite_frontdoor_response(
		request_id="phase3-2-customer-commercial-active",
		message="show top 5 customers by revenue for sales orders last month",
		company_name=company_name,
	)
	legacy_surface = maybe_build_governed_composite_frontdoor_response(
		request_id="phase3-2-customer-commercial-legacy-surface",
		message="show top 5 customers by revenue last month",
		company_name=company_name,
	)
	implied_basis = maybe_build_governed_composite_frontdoor_response(
		request_id="phase3-2-customer-commercial-implied-basis",
		message="show top 5 customers by average order value last month",
		company_name=company_name,
	)
	clarify_primary = maybe_build_governed_composite_frontdoor_response(
		request_id="phase3-2-customer-commercial-primary",
		message="show top customers for sales orders last month",
		company_name=company_name,
	)
	ok = (
		_clean_text((((active.get("composite_artifact") or {}).get("composite_id")) if isinstance(active, dict) else ""))
		== "customer_commercial_ranking_sales_order_composite"
		and isinstance((active.get("composite_artifact") or {}).get("rows"), list)
		and len((active.get("composite_artifact") or {}).get("rows") or []) > 0
		and not legacy_surface
		and _clean_text((((implied_basis.get("composite_artifact") or {}).get("composite_id")) if isinstance(implied_basis, dict) else ""))
		== "customer_commercial_ranking_sales_order_composite"
		and _clean_text((((clarify_primary.get("clarification_signal_payload") or {}).get("reason_type")) if isinstance(clarify_primary, dict) else ""))
		== "composite_family_variation"
	)
	return {
		"ok": ok,
		"active": _summary(active),
		"legacy_surface": _summary(legacy_surface),
		"implied_basis": _summary(implied_basis),
		"clarify_primary": _summary(clarify_primary),
	}


def run_governed_product_commercial_composite_probe() -> Dict[str, Any]:
	def _summary(payload: Dict[str, Any]) -> Dict[str, Any]:
		if not isinstance(payload, dict):
			return {}
		composite_artifact = payload.get("composite_artifact") if isinstance(payload.get("composite_artifact"), dict) else {}
		rows = composite_artifact.get("rows") if isinstance(composite_artifact.get("rows"), list) else []
		first_row = dict(rows[0] or {}) if rows else {}
		metric_values = first_row.get("metric_values") if isinstance(first_row.get("metric_values"), dict) else {}
		return {
			"frontdoor_answer": _clean_text(payload.get("frontdoor_answer")),
			"family_resolution": dict(payload.get("family_resolution") or {}),
			"artifact_resolution": dict(payload.get("artifact_resolution") or {}),
			"clarification_signal_payload": dict(payload.get("clarification_signal_payload") or {}),
			"composite_artifact": {
				"composite_id": _clean_text(composite_artifact.get("composite_id")),
				"row_count": len(rows),
				"first_row_entity": _clean_text(
					first_row.get("entity_name")
					or first_row.get("item_name")
					or first_row.get("entity")
					or first_row.get("item_code")
				),
				"first_row_metric_values": {
					metric_id: {
						"value": metric_payload.get("value"),
						"display_value": _clean_text(metric_payload.get("display_value")),
					}
					for metric_id, metric_payload in metric_values.items()
					if isinstance(metric_payload, dict)
				},
			},
		}

	company_name = "Mingalar Mobile Distribution Co., Ltd."
	active = maybe_build_governed_composite_frontdoor_response(
		request_id="phase3-3-product-commercial-active",
		message="show top 5 products by revenue for sales orders last month",
		company_name=company_name,
	)
	legacy_surface = maybe_build_governed_composite_frontdoor_response(
		request_id="phase3-3-product-commercial-legacy-surface",
		message="show top 5 products by revenue last month",
		company_name=company_name,
	)
	clarify_basis = maybe_build_governed_composite_frontdoor_response(
		request_id="phase3-3-product-commercial-basis",
		message="show top 5 products by average selling price last month",
		company_name=company_name,
	)
	clarify_primary = maybe_build_governed_composite_frontdoor_response(
		request_id="phase3-3-product-commercial-primary",
		message="show top products for sales invoices last month",
		company_name=company_name,
	)
	ok = (
		_clean_text((((active.get("composite_artifact") or {}).get("composite_id")) if isinstance(active, dict) else ""))
		== "product_commercial_ranking_sales_order_composite"
		and isinstance((active.get("composite_artifact") or {}).get("rows"), list)
		and len((active.get("composite_artifact") or {}).get("rows") or []) > 0
		and not legacy_surface
		and _clean_text((((clarify_basis.get("clarification_signal_payload") or {}).get("reason_type")) if isinstance(clarify_basis, dict) else ""))
		== "composite_family_variation"
		and _clean_text((((clarify_primary.get("clarification_signal_payload") or {}).get("reason_type")) if isinstance(clarify_primary, dict) else ""))
		== "composite_family_variation"
	)
	return {
		"ok": ok,
		"active": _summary(active),
		"legacy_surface": _summary(legacy_surface),
		"clarify_basis": _summary(clarify_basis),
		"clarify_primary": _summary(clarify_primary),
	}
