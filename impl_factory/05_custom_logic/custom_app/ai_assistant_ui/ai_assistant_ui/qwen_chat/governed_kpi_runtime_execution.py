from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None

from ai_assistant_ui.qwen_chat.business_definition_state import (
	BusinessDefinitionStateContract,
	GovernedFormulaStateContract,
	build_business_definition_state_contract,
	resolve_business_definition_state,
	resolve_governed_formula_state,
)
from ai_assistant_ui.qwen_chat.compiler import _date_range_from_time_scope
from ai_assistant_ui.qwen_chat.contracts import (
	FrontDoorIntentGateContract,
	build_clarification_signal_contract,
)
from ai_assistant_ui.qwen_chat.clarification_translation import (
	render_shared_choice_list_clarification,
)
from ai_assistant_ui.qwen_chat.customer_kpi_runtime_support import (
	current_date_iso,
	get_customer_kpi_scalar_snapshot,
	list_customer_kpi_rows,
	resolve_customer_scope_from_message,
)
from ai_assistant_ui.qwen_chat.defaults_repository import single_company_name
from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import (
	SemanticFrontDoorIntent,
	SemanticFrontDoorResult,
)
from ai_assistant_ui.qwen_chat.entity_period_aggregation_support import (
	list_entity_period_commercial_rows,
)
from ai_assistant_ui.qwen_chat.governed_kpi_execution_state import (
	GovernedKpiExecutionStateContract,
	GovernedKpiRankingArtifactContract,
	GovernedKpiValueArtifactContract,
	build_governed_kpi_ranking_artifact_contract,
	build_governed_kpi_value_artifact_contract,
	resolve_governed_kpi_execution_state,
)
from ai_assistant_ui.qwen_chat.metadata import (
	get_frontdoor_intent_spec,
	get_report_spec,
	list_business_definition_specs,
	list_semantic_resolution_alias_entries,
)
from ai_assistant_ui.qwen_chat.ranking_limit_parser import extract_requested_top_n
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys
from ai_assistant_ui.qwen_chat.semantic_resolution_registry import (
	best_semantic_slot_alias,
	semantic_slot_alias_phrases_for_value,
)


_GENERIC_VALUE_REQUEST_PATTERN = re.compile(
	r"^(?:please\s+)?(?:show|give(?:\s+me)?|tell(?:\s+me)?|calculate|compute|display|provide|share)\b",
	re.IGNORECASE,
)
_WHAT_IS_VALUE_REQUEST_PATTERN = re.compile(r"^(?:please\s+)?(?:can you\s+)?what is\b", re.IGNORECASE)
_BUSINESS_PURPOSE_SUFFIX_PATTERN = re.compile(r"\s+and\s+why\s+does\s+it\s+matter\s*\??$", re.IGNORECASE)
_PERIOD_SCOPE_ORDER = (
	"last_month",
	"current_fiscal_year_to_date",
	"last_year",
)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _normalize_text(value: Any) -> str:
	return " ".join(_clean_text(value).lower().split())


def _tokenize(value: Any) -> List[str]:
	return re.findall(r"[a-z0-9]+", _normalize_text(value))


def _money(value: Any) -> str:
	try:
		numeric = float(value or 0.0)
	except Exception:
		numeric = 0.0
	return f"{numeric:,.2f}".rstrip("0").rstrip(".")


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _percent(value: Any) -> str:
	try:
		numeric = float(value or 0.0)
	except Exception:
		numeric = 0.0
	return f"{numeric * 100:,.2f}".rstrip("0").rstrip(".")


def _days_text(value: Any) -> str:
	try:
		numeric = int(float(value or 0))
	except Exception:
		numeric = 0
	return f"{numeric:,} day" if numeric == 1 else f"{numeric:,} days"


def _count_text(value: Any) -> str:
	try:
		numeric = float(value or 0.0)
	except Exception:
		numeric = 0.0
	if abs(numeric - int(numeric)) < 0.000001:
		return f"{int(numeric):,}"
	return f"{numeric:,.2f}".rstrip("0").rstrip(".")


def _format_title_case_token(value: Any) -> str:
	text = _clean_text(value).replace("_", " ")
	text = re.sub(r"\s+", " ", text)
	return text.title()


def _format_governed_phrase(value: Any) -> str:
	text = _clean_text(value).lower()
	phrase_map = {
		"transaction_period": "Transaction period",
		"current_fiscal_year_to_date": "Current Fiscal Year to Date",
		"last_month": "Last Month",
		"last_year": "Last Year",
		"latest_value": "Latest value",
		"ratio_of_sums": "Ratio of sums",
	}
	if text in phrase_map:
		return phrase_map[text]
	return _format_title_case_token(value)


def _lower_first(text: Any) -> str:
	value = _clean_text(text)
	if not value:
		return ""
	return value[:1].lower() + value[1:]


def _sentence(text: Any) -> str:
	value = _clean_text(text)
	if not value:
		return ""
	return value if value.endswith((".", "!", "?")) else f"{value}."


def _company_scope_matches(values: Any, company_name: str) -> bool:
	scope_values = [_normalize_text(item) for item in (values or []) if _normalize_text(item)]
	if not scope_values:
		return True
	normalized_company = _normalize_text(company_name)
	return not normalized_company or "global" in scope_values or normalized_company in scope_values


def _current_company_name(explicit_company_name: str) -> str:
	company_name = _clean_text(explicit_company_name)
	return company_name or single_company_name()


def _business_purpose_requested(message: str) -> bool:
	return bool(_BUSINESS_PURPOSE_SUFFIX_PATTERN.search(_clean_text(message)))


def _with_business_purpose_suffix_removed(message: str) -> str:
	return _BUSINESS_PURPOSE_SUFFIX_PATTERN.sub("", _clean_text(message)).strip()


def _runtime_detail_requested(message: str) -> bool:
	normalized_message = _normalize_text(message)
	if not normalized_message:
		return False
	return bool(
		re.search(
			r"\b(how was|how is|calculated|calculate|formula|basis|show governed basis|explain calculation)\b",
			normalized_message,
			re.IGNORECASE,
		)
	)


def _tokens_match_subsequence(term_tokens: List[str], message_tokens: List[str]) -> Tuple[bool, int]:
	if not term_tokens or not message_tokens:
		return False, 0
	start_index = -1
	position = 0
	for token in term_tokens:
		found = False
		while position < len(message_tokens):
			if message_tokens[position] == token:
				if start_index < 0:
					start_index = position
				position += 1
				found = True
				break
			position += 1
		if not found:
			return False, 0
	end_index = max(position - 1, start_index)
	return True, max(1, end_index - start_index + 1)


def _definition_match_score(term_tokens: List[str], span: int) -> int:
	return (len(term_tokens) * 100) - int(max(0, span))


def _match_definition_candidates_from_message(
	*,
	message: str,
	company_name: str,
	allowed_time_bases: set[str] | None = None,
	allowed_entity_grains: set[str] | None = None,
) -> List[Dict[str, Any]]:
	message_tokens = _tokenize(message)
	if not message_tokens:
		return []
	best_by_definition: Dict[str, Dict[str, Any]] = {}
	normalized_time_bases = {
		_clean_text(value)
		for value in (allowed_time_bases or set())
		if _clean_text(value)
	}
	normalized_entity_grains = {
		_clean_text(value)
		for value in (allowed_entity_grains or set())
		if _clean_text(value)
	}
	for item in list_business_definition_specs():
		time_basis = _clean_text(item.get("time_basis"))
		entity_grain = _clean_text(item.get("entity_grain"))
		if normalized_time_bases and time_basis not in normalized_time_bases:
			continue
		if normalized_entity_grains and entity_grain not in normalized_entity_grains:
			continue
		if not _company_scope_matches(item.get("company_scope"), company_name):
			continue
		definition_id = _clean_text(item.get("definition_id"))
		if not definition_id:
			continue
		for raw_term in (item.get("lookup_terms") or []):
			lookup_term = _clean_text(raw_term)
			for variant in _lookup_term_variants(raw_term):
				term_tokens = _tokenize(variant)
				matched, span = _tokens_match_subsequence(term_tokens, message_tokens)
				if not matched:
					continue
				score = _definition_match_score(term_tokens, span)
				current = best_by_definition.get(definition_id)
				if current is None or score > int(current.get("score") or 0):
					best_by_definition[definition_id] = {
						"definition_id": definition_id,
						"label": _clean_text(item.get("label")),
						"lookup_term": lookup_term,
						"score": score,
					}
	if not best_by_definition:
		return []
	best_score = max(int(item.get("score") or 0) for item in best_by_definition.values())
	best_matches = [
		dict(item)
		for item in best_by_definition.values()
		if int(item.get("score") or 0) == best_score
	]
	listing_view_basis = _extract_listing_view_basis(message)
	if listing_view_basis and len(best_matches) > 1:
		filtered_matches = [
			item
			for item in best_matches
			if _definition_listing_view_canonical(_clean_text(item.get("definition_id"))) == listing_view_basis
		]
		if filtered_matches:
			return filtered_matches
	return best_matches


def _match_period_kpi_definitions_from_message(
	*,
	message: str,
	company_name: str,
) -> List[Dict[str, Any]]:
	return _match_definition_candidates_from_message(
		message=message,
		company_name=company_name,
		allowed_time_bases={"transaction_period"},
	)


def _match_customer_kpi_definitions_from_message(
	*,
	message: str,
	company_name: str,
) -> List[Dict[str, Any]]:
	return _match_definition_candidates_from_message(
		message=message,
		company_name=company_name,
		allowed_time_bases={"as_of_date", "customer_created_at", "first_sales_order_date", "first_sales_invoice_date"},
		allowed_entity_grains={"customer"},
	)


def _resolve_definition_state_from_message_match(
	*,
	message: str,
	company_name: str,
) -> BusinessDefinitionStateContract | None:
	matches = _match_period_kpi_definitions_from_message(message=message, company_name=company_name)
	if not matches:
		return None
	if len(matches) == 1:
		return resolve_business_definition_state(
			_clean_text(matches[0].get("lookup_term")),
			lookup_mode="lookup_term",
			company_name=company_name,
		)
	lookup_terms = {
		_clean_text(item.get("lookup_term"))
		for item in matches
		if _clean_text(item.get("lookup_term"))
	}
	if len(lookup_terms) == 1:
		return resolve_business_definition_state(
			lookup_terms.pop(),
			lookup_mode="lookup_term",
			company_name=company_name,
		)
	return build_business_definition_state_contract(
		lookup_value=_clean_text(message),
		lookup_mode="lookup_term",
		requested_company_name=company_name,
		resolution_state="ambiguous",
		match_count=len(matches),
		matched_definition_ids=[
			_clean_text(item.get("definition_id"))
			for item in matches
			if _clean_text(item.get("definition_id"))
		],
		reason="Multiple governed period KPI definitions match the current message.",
		candidate_definitions=[
			{
				"definition_id": _clean_text(item.get("definition_id")),
				"label": _clean_text(item.get("label")),
				"activation_state": "active",
				"company_scope": [company_name],
				"clarify_policy": "clarify_document_basis",
				"blocked_reason": "",
			}
			for item in matches
		],
	)


def _time_scope_alias_matches_message(message: str, alias: str) -> bool:
	value = _normalize_text(message)
	target = _normalize_text(alias)
	if not value or not target:
		return False
	pattern = r"(^|[^a-z0-9])" + re.escape(target) + r"([^a-z0-9]|$)"
	return bool(re.search(pattern, value))


def _extract_canonical_alias(slot_name: str, message: str) -> str:
	return best_semantic_slot_alias(slot_name, message)


def _extract_period_time_scope(message: str) -> str:
	canonical_value = _extract_canonical_alias("time_scope", message)
	return canonical_value if canonical_value in _PERIOD_SCOPE_ORDER else ""


def _extract_listing_view_basis(message: str) -> str:
	return _extract_canonical_alias("listing_view", message)


def _lookup_term_variants(raw_term: Any) -> List[str]:
	clean_term = _clean_text(raw_term)
	if not clean_term:
		return []
	variants = {clean_term}
	for entry in list_semantic_resolution_alias_entries("listing_view"):
		canonical_value = _clean_text(entry.get("canonical_value"))
		if not canonical_value:
			continue
		canonical_phrase = canonical_value.replace("_", " ")
		pattern = re.compile(r"(^|[^a-z0-9])" + re.escape(canonical_phrase) + r"([^a-z0-9]|$)", re.IGNORECASE)
		if not pattern.search(clean_term):
			continue
		for alias in (entry.get("aliases") or []):
			alias_text = _clean_text(alias)
			if not alias_text:
				continue
			variants.add(pattern.sub(lambda match: f"{match.group(1)}{alias_text}{match.group(2)}", clean_term))
	return [value for value in variants if _clean_text(value)]


def _definition_listing_view_canonical(definition_id: str) -> str:
	for item in list_business_definition_specs():
		if _clean_text(item.get("definition_id")) != _clean_text(definition_id):
			continue
		source_of_truth = dict(item.get("source_of_truth") or {})
		report_names: List[str] = []
		for key in ("report_name", "report_names"):
			value = source_of_truth.get(key)
			if isinstance(value, list):
				report_names.extend(_clean_text(entry) for entry in value if _clean_text(entry))
			elif _clean_text(value):
				report_names.append(_clean_text(value))
		for report_name in report_names:
			report_spec = get_report_spec(report_name)
			direct_query = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
			doctype = _clean_text(direct_query.get("doctype"))
			if doctype:
				return _normalize_text(doctype).replace(" ", "_")
		break
	return ""


def _listing_view_aliases_for_canonical(canonical_value: str) -> List[str]:
	return semantic_slot_alias_phrases_for_value("listing_view", canonical_value)


def _looks_like_runtime_value_request(
	message: str,
	*,
	requested_time_scope: str,
	definition_state: BusinessDefinitionStateContract | None = None,
) -> bool:
	text = _clean_text(message)
	if not text:
		return False
	if requested_time_scope:
		return True
	if _GENERIC_VALUE_REQUEST_PATTERN.match(text):
		return True
	if not _WHAT_IS_VALUE_REQUEST_PATTERN.match(text):
		return False
	if definition_state is None:
		return False
	return bool(_extract_listing_view_basis(text))


def _looks_like_customer_runtime_value_request(
	message: str,
	*,
	is_ranking_request: bool,
) -> bool:
	text = _clean_text(message)
	if not text:
		return False
	if is_ranking_request:
		return True
	if _runtime_detail_requested(text):
		return True
	if _GENERIC_VALUE_REQUEST_PATTERN.match(text) or _WHAT_IS_VALUE_REQUEST_PATTERN.match(text):
		return True
	return bool(_customer_metric_alias_keys(text).intersection({"credit_limit_status", "credit_limit_utilization"}))


def _period_scope_phrase(canonical_scope: str) -> str:
	scope = _clean_text(canonical_scope)
	if scope == "last_month":
		return "last month"
	if scope == "current_fiscal_year_to_date":
		return "current fiscal year to date"
	if scope == "last_year":
		return "last year"
	return _normalize_text(scope)


def _period_scope_label(canonical_scope: str) -> str:
	return _format_governed_phrase(canonical_scope)


def _period_scope_options() -> List[str]:
	return [_period_scope_label(value) for value in _PERIOD_SCOPE_ORDER]


def _formula_basis_phrase(
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
) -> str:
	source_of_truth = dict(definition_state.source_of_truth or {})
	numerator = _clean_text(source_of_truth.get("numerator_metric") or source_of_truth.get("numerator_basis"))
	denominator = _clean_text(source_of_truth.get("denominator_metric") or source_of_truth.get("denominator_basis"))
	if numerator and denominator:
		return f"{numerator} / {denominator}"
	input_metrics = [_clean_text(value) for value in (formula_state.input_metrics or []) if _clean_text(value)]
	if len(input_metrics) == 2 and _clean_text(formula_state.formula_type) in {"ratio", "sum_divided_by_count"}:
		return f"{_format_title_case_token(input_metrics[0])} / {_format_title_case_token(input_metrics[1])}"
	return ""


def _source_report_phrase(
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
) -> str:
	source_of_truth = dict(definition_state.source_of_truth or {})
	report_names: List[str] = []
	for key in ("report_name", "report_names"):
		value = source_of_truth.get(key)
		if isinstance(value, list):
			report_names.extend(_clean_text(item) for item in value if _clean_text(item))
		elif _clean_text(value):
			report_names.append(_clean_text(value))
	if not report_names:
		report_names = [_clean_text(value) for value in (formula_state.source_reports or []) if _clean_text(value)]
	if not report_names:
		return ""
	if len(report_names) == 1:
		return report_names[0]
	if len(report_names) == 2:
		return f"{report_names[0]} and {report_names[1]}"
	return ", ".join(report_names[:-1]) + f", and {report_names[-1]}"


def _definition_business_purpose(definition_id: str) -> str:
	for item in list_business_definition_specs():
		if _clean_text(item.get("definition_id")) == _clean_text(definition_id):
			return _clean_text(item.get("business_purpose"))
	return ""


def _specific_lookup_term_for_definition(
	*,
	definition_id: str,
	fallback_label: str,
	ambiguous_lookup_value: str = "",
) -> str:
	label_tokens = set(_tokenize(fallback_label))
	ambiguous_lookup = _normalize_text(ambiguous_lookup_value)
	best_term = ""
	best_score = -1
	best_length = -1
	for item in list_business_definition_specs():
		if _clean_text(item.get("definition_id")) != _clean_text(definition_id):
			continue
		for raw_term in (item.get("lookup_terms") or []):
			clean_term = _clean_text(raw_term)
			if not clean_term:
				continue
			normalized_term = _normalize_text(clean_term)
			if not normalized_term or normalized_term == ambiguous_lookup:
				continue
			term_tokens = set(_tokenize(clean_term))
			score = len(term_tokens & label_tokens)
			if score > best_score or (score == best_score and len(term_tokens) > best_length):
				best_term = clean_term
				best_score = score
				best_length = len(term_tokens)
		break
	return best_term or _clean_text(fallback_label)


def _definition_rule_notes(
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
) -> List[str]:
	from ai_assistant_ui.qwen_chat.metadata import list_business_rule_specs

	notes: List[str] = []
	company_name = _clean_text(definition_state.requested_company_name)
	for item in list_business_rule_specs():
		if _clean_text(item.get("activation_state")) != "active":
			continue
		if not _company_scope_matches(item.get("company_scope"), company_name):
			continue
		scope_type = _clean_text(item.get("scope_type"))
		scope_reference = _clean_text(item.get("scope_reference"))
		statement = _clean_text(item.get("policy_statement"))
		if not statement:
			continue
		if scope_type == "definition" and scope_reference == _clean_text(definition_state.definition_id):
			notes.append(statement)
		if scope_type == "formula" and scope_reference == _clean_text(formula_state.formula_id):
			notes.append(statement)
	return notes


def _threshold_notes(formula_id: str) -> List[str]:
	from ai_assistant_ui.qwen_chat.metadata import list_business_threshold_specs_for_formula

	notes: List[str] = []
	for item in list_business_threshold_specs_for_formula(formula_id):
		activation_state = _clean_text(item.get("activation_state"))
		labels = [
			_clean_text(band.get("label"))
			for band in (item.get("bands") or [])
			if isinstance(band, dict) and _clean_text(band.get("label"))
		]
		if activation_state == "active":
			if labels:
				notes.append(
					f"Threshold semantics are active with governed bands {', '.join(f'`{label}`' for label in labels)}."
				)
			else:
				notes.append("Threshold semantics are active for this KPI.")
		else:
			blocked_reason = _clean_text(item.get("blocked_reason"))
			if blocked_reason:
				notes.append(f"Threshold semantics remain blocked for user-facing runtime use: {blocked_reason}")
	return notes


def _natural_threshold_summary(formula_id: str, *, artifact_threshold_state: Dict[str, Any] | None = None) -> str:
	threshold_state = dict(artifact_threshold_state or {})
	matched_band = _clean_text(threshold_state.get("matched_band_label"))
	if matched_band == "limit_exceeded":
		return "This customer is currently above the approved credit limit."
	if matched_band == "within_limit":
		return "This customer is currently within the approved credit limit."
	for note in _threshold_notes(formula_id):
		blocked_prefix = "Threshold semantics remain blocked for user-facing runtime use:"
		if note.startswith(blocked_prefix):
			reason = _clean_text(note.split(":", 1)[1] if ":" in note else "")
			if reason:
				return _sentence(reason[:1].upper() + reason[1:])
	return ""


def _source_documents_phrase(source_report_phrase: str) -> str:
	value = _clean_text(source_report_phrase).lower()
	if "sales order" in value:
		return "submitted sales orders"
	if "sales invoice" in value:
		return "submitted sales invoices"
	if "purchase order" in value:
		return "submitted purchase orders"
	return "submitted documents"


def _source_date_value(artifact: GovernedKpiValueArtifactContract, metric_key: str) -> str:
	for evidence in artifact.source_evidence:
		if _clean_text(evidence.get("metric_key")) == metric_key:
			return _clean_text(evidence.get("value"))
	return ""


def _build_period_requested_scope(requested_time_scope: str) -> Dict[str, Any]:
	start_date, end_date = _date_range_from_time_scope(requested_time_scope)
	if not start_date or not end_date:
		return {}
	return {
		"requested_time_scope": requested_time_scope,
		"has_period_scope": True,
		"period_start": start_date,
		"period_end": end_date,
	}


def _extract_as_of_date_scope(message: str) -> str:
	explicit_iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", _clean_text(message))
	if explicit_iso_match:
		return _clean_text(explicit_iso_match.group(1))
	if _extract_canonical_alias("time_scope", message) == "as_of_today":
		return current_date_iso()
	return ""


def _ranking_subject(message: str) -> str:
	return _extract_canonical_alias("ranking_subject", message)


def _looks_like_customer_ranking_request(message: str) -> bool:
	normalized_message = _normalize_text(message)
	if _ranking_subject(message) != "customer":
		return False
	if re.search(r"\b(top|highest|lowest|ranking|rank)\b", normalized_message, re.IGNORECASE):
		return True
	if re.search(r"\bcustomers\b", normalized_message, re.IGNORECASE) and re.search(
		r"\b(by|above|below|over|under|exceeded|within|limit)\b",
		normalized_message,
		re.IGNORECASE,
	):
		return True
	if re.search(
		r"\b(which|show|list)\s+customers\b.*\b(above|below|over|under|exceeded|within)\b",
		normalized_message,
		re.IGNORECASE,
	):
		return True
	return False


def _requested_top_n(message: str, default_limit: int = 10) -> int:
	return extract_requested_top_n(message, default_limit=default_limit, max_limit=100)


def _customer_metric_alias_keys(message: str) -> set[str]:
	return set(
		detect_canonical_keys(
			message,
			capability_id="accounts_receivable_read",
			dimension_or_metric="metric",
		)
	)


def _looks_like_deictic_customer_scope(message: str) -> bool:
	return bool(
		re.search(
			r"\b(this|that)\s+customer(?:'s)?\b|\b(this|that)\s+(account|client|party)\b",
			_normalize_text(message),
			re.IGNORECASE,
		)
	)


def _grounded_customer_scope_from_turn(grounded_turn: Dict[str, Any] | None) -> Dict[str, Any]:
	if not isinstance(grounded_turn, dict):
		return {}
	known_entities = grounded_turn.get("known_entities")
	if isinstance(known_entities, list):
		for item in known_entities:
			if not isinstance(item, dict):
				continue
			if _clean_text(item.get("entity_type")).lower() != "customer":
				continue
			customer_key = _clean_text(item.get("code") or item.get("customer") or item.get("name"))
			customer_label = _clean_text(item.get("name") or item.get("label") or customer_key)
			if customer_key:
				return {
					"customer": customer_key,
					"customer_name": customer_label or customer_key,
					"entity_name": customer_key,
					"entity_label": customer_label or customer_key,
					"matched_alias": customer_label or customer_key,
					"has_customer_scope": True,
					"scope_source": "grounded_turn",
				}
	filters = grounded_turn.get("filters")
	if isinstance(filters, dict) and _clean_text(filters.get("entity_type")).lower() == "customer":
		customer_key = _clean_text(filters.get("entity_key") or filters.get("customer"))
		if customer_key:
			return {
				"customer": customer_key,
				"customer_name": customer_key,
				"entity_name": customer_key,
				"entity_label": customer_key,
				"matched_alias": customer_key,
				"has_customer_scope": True,
				"scope_source": "grounded_turn",
			}
	return {}


def _resolve_customer_definition_state_from_message(
	*,
	message: str,
	company_name: str,
	is_ranking_request: bool = False,
) -> BusinessDefinitionStateContract | None:
	matches = _match_customer_kpi_definitions_from_message(message=message, company_name=company_name)
	if not matches:
		metric_aliases = _customer_metric_alias_keys(message)
		if metric_aliases.intersection({"credit_limit_status", "credit_limit_utilization"}):
			return resolve_business_definition_state(
				"credit utilization",
				lookup_mode="lookup_term",
				company_name=company_name,
			)
		return None
	if is_ranking_request:
		supported_ranking_matches = [
			item
			for item in matches
			if _clean_text(item.get("definition_id")) in {
				"credit_utilization_customer_as_of_date",
				"customer_overdue_amount_as_of_date",
				"customer_overdue_ratio_as_of_date",
			}
		]
		if supported_ranking_matches:
			matches = supported_ranking_matches
	if len(matches) == 1:
		return resolve_business_definition_state(
			_clean_text(matches[0].get("lookup_term")),
			lookup_mode="lookup_term",
			company_name=company_name,
		)
	lookup_terms = {
		_clean_text(item.get("lookup_term"))
		for item in matches
		if _clean_text(item.get("lookup_term"))
	}
	if len(lookup_terms) == 1:
		return resolve_business_definition_state(
			lookup_terms.pop(),
			lookup_mode="lookup_term",
			company_name=company_name,
		)
	return build_business_definition_state_contract(
		lookup_value=_clean_text(message),
		lookup_mode="lookup_term",
		requested_company_name=company_name,
		resolution_state="ambiguous",
		match_count=len(matches),
		matched_definition_ids=[
			_clean_text(item.get("definition_id"))
			for item in matches
			if _clean_text(item.get("definition_id"))
		],
		reason="Multiple governed customer KPI definitions match the current message.",
		candidate_definitions=[
			{
				"definition_id": _clean_text(item.get("definition_id")),
				"label": _clean_text(item.get("label")),
				"activation_state": "active",
				"company_scope": [company_name],
				"clarify_policy": "clarify_basis",
				"blocked_reason": "",
			}
			for item in matches
		],
	)


def _customer_execution_shape(message: str) -> str:
	return "customer_as_of_ranking" if _looks_like_customer_ranking_request(message) else "customer_as_of_scalar"


def _build_customer_requested_scope(message: str, grounded_turn: Dict[str, Any] | None = None) -> Dict[str, Any]:
	scope = resolve_customer_scope_from_message(message)
	if not bool(scope.get("has_customer_scope")) and _looks_like_deictic_customer_scope(message):
		scope = _grounded_customer_scope_from_turn(grounded_turn)
	as_of_date = _extract_as_of_date_scope(message) or current_date_iso()
	scope.update(
		{
			"as_of_date": as_of_date,
			"has_as_of_date": bool(as_of_date),
		}
	)
	if _looks_like_customer_ranking_request(message):
		scope.update(
			{
				"ranking_limit": _requested_top_n(message),
				"ranking_subject": "customer",
			}
		)
	return scope


def _customer_continuation_suffix(requested_scope: Dict[str, Any]) -> str:
	parts: List[str] = []
	customer_label = _clean_text(
		requested_scope.get("customer_name")
		or requested_scope.get("entity_label")
		or requested_scope.get("customer")
	)
	as_of_date = _clean_text(requested_scope.get("as_of_date"))
	if customer_label:
		parts.append(f"for {customer_label}")
	if as_of_date:
		parts.append(f"as of {as_of_date}")
	return " ".join(parts).strip()


def _render_missing_customer_answer(
	*,
	definition_state: BusinessDefinitionStateContract,
	as_of_date: str,
) -> str:
	answer_lines = [
		f"I can calculate {definition_state.label.lower()} as of {as_of_date}, but I still need the customer.",
		"",
		"You can either:",
		"- Ask again with the customer name",
		"- Open a customer detail first, then ask a deictic follow-up like `what is this customer's overdue ratio?`",
	]
	return "\n".join(answer_lines).strip()


def _build_missing_customer_clarification_signal(
	*,
	request_id: str,
	definition_state: BusinessDefinitionStateContract,
	as_of_date: str,
	answer_text: str,
) -> Dict[str, Any]:
	specific_lookup_term = _specific_lookup_term_for_definition(
		definition_id=definition_state.definition_id,
		fallback_label=definition_state.label,
		ambiguous_lookup_value=_clean_text(definition_state.lookup_value),
	)
	continuation_suffix = "for {customer}"
	if _clean_text(as_of_date):
		continuation_suffix = f"{continuation_suffix} as of {as_of_date}"
	resolved_message_template = _execution_continuation_message(
		lookup_term=specific_lookup_term or definition_state.label,
		continuation_suffix=continuation_suffix,
	)
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="frontdoor",
		reason_type="customer_scope_missing",
		user_question=answer_text,
		suggested_options=[],
		internal_reason="The governed customer KPI runtime request needs an explicit customer scope before execution can proceed.",
		internal_details={
			"continuation_lane": "front_door",
			"continuation_intent_class": "governed_kpi_value",
			"entity_grain": "customer",
			"resolved_slot_key": "selected_customer",
			"resolved_message_placeholder": "customer",
			"resolved_message_template": resolved_message_template,
			"definition_id": definition_state.definition_id,
			"requested_as_of_date": _clean_text(as_of_date),
		},
	).to_payload()


def _direct_query_metric_field(report_name: str, metric_key: str) -> str:
	report_spec = get_report_spec(report_name)
	direct_query = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	fields = [_clean_text(value) for value in (direct_query.get("fields") or []) if _clean_text(value)]
	clean_metric = _clean_text(metric_key)
	if clean_metric in fields:
		return clean_metric
	return ""


def _safe_sql_identifier(value: str) -> str:
	clean = _clean_text(value)
	if not clean or not re.fullmatch(r"[A-Za-z0-9_ ]+", clean):
		raise ValueError(f"Unsupported governed SQL identifier: {value!r}")
	return clean


def _aggregate_direct_query_sum_and_count(
	*,
	report_name: str,
	company_name: str,
	from_date: str,
	to_date: str,
	sum_field: str,
) -> Dict[str, Any]:
	if frappe is None:
		return {}
	report_spec = get_report_spec(report_name)
	direct_query = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	doctype = _safe_sql_identifier(direct_query.get("doctype"))
	date_field = _safe_sql_identifier(direct_query.get("date_field"))
	sum_field_name = _safe_sql_identifier(sum_field)
	fixed_filters = direct_query.get("fixed_filters") if isinstance(direct_query.get("fixed_filters"), dict) else {}
	where_clauses: List[str] = []
	params: List[Any] = []
	for fieldname, value in fixed_filters.items():
		clean_fieldname = _safe_sql_identifier(fieldname)
		if isinstance(value, (str, int, float, bool)):
			where_clauses.append(f"`{clean_fieldname}` = %s")
			params.append(value)
		else:
			raise ValueError(f"Unsupported fixed filter value for governed KPI aggregate: {fieldname!r}")
	where_clauses.append("`company` = %s")
	params.append(company_name)
	where_clauses.append(f"`{date_field}` between %s and %s")
	params.extend([from_date, to_date])
	rows = frappe.db.sql(
		f"""
		select
			count(`name`) as document_count,
			coalesce(sum(`{sum_field_name}`), 0) as numerator_value
		from `tab{doctype}`
		where {" and ".join(where_clauses)}
		""",
		tuple(params),
		as_dict=True,
	)
	row = dict(rows[0] or {}) if rows else {}
	document_count = int(float(row.get("document_count") or 0))
	numerator_value = float(row.get("numerator_value") or 0.0)
	return {
		"report_name": report_name,
		"company": company_name,
		"from_date": from_date,
		"to_date": to_date,
		"document_count": document_count,
		"numerator_value": numerator_value,
	}


def _execute_company_period_value_artifact(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	execution_state: GovernedKpiExecutionStateContract,
	requested_scope: Dict[str, Any],
) -> GovernedKpiValueArtifactContract:
	company_name = _clean_text(definition_state.requested_company_name)
	period_start = _clean_text(requested_scope.get("period_start"))
	period_end = _clean_text(requested_scope.get("period_end"))
	execution_id = _clean_text(execution_state.execution_id)
	if execution_id == "collection_ratio_sales_invoice_period_company_scalar_execution":
		from ai_assistant_ui.qwen_chat.collections_support import (
			compute_collection_ratio_by_sales_invoice_period,
		)

		result = compute_collection_ratio_by_sales_invoice_period(
			company=company_name,
			from_date=period_start,
			to_date=period_end,
		)
		return build_governed_kpi_value_artifact_contract(
			execution_state=execution_state,
			entity_grain=definition_state.entity_grain,
			scope={"company": company_name},
			period_start=period_start,
			period_end=period_end,
			value=result.get("collection_ratio"),
			display_value=f"{_percent(result.get('collection_ratio'))}%",
			numerator_label="Allocated Customer Receipt Amount",
			numerator_value=result.get("allocated_customer_receipt_amount"),
			denominator_label="Sales Invoice Grand Total",
			denominator_value=result.get("sales_invoice_grand_total"),
			source_evidence=[
				{
					"report_name": "Sales Invoice List",
					"metric_key": "sales_invoice_grand_total",
					"value": float(result.get("sales_invoice_grand_total") or 0.0),
				},
				{
					"report_name": "Payment Entry List",
					"metric_key": "allocated_customer_receipt_amount",
					"value": float(result.get("allocated_customer_receipt_amount") or 0.0),
				},
			],
			status="active_value",
		)

	report_name = _clean_text((execution_state.source_reports or [""])[0])
	sum_field = _direct_query_metric_field(report_name, "grand_total")
	aggregate = _aggregate_direct_query_sum_and_count(
		report_name=report_name,
		company_name=company_name,
		from_date=period_start,
		to_date=period_end,
		sum_field=sum_field,
	)
	document_count = int(aggregate.get("document_count") or 0)
	numerator_value = float(aggregate.get("numerator_value") or 0.0)
	value = (numerator_value / float(document_count)) if document_count > 0 else 0.0
	return build_governed_kpi_value_artifact_contract(
		execution_state=execution_state,
		entity_grain=definition_state.entity_grain,
		scope={"company": company_name},
		period_start=period_start,
		period_end=period_end,
		value=value,
		display_value=f"{_money(value)} MMK",
		numerator_label="Grand Total",
		numerator_value=numerator_value,
		denominator_label="Submitted Document Count",
		denominator_value=document_count,
		source_evidence=[
			{
				"report_name": report_name,
				"metric_key": "grand_total",
				"value": numerator_value,
			},
			{
				"report_name": report_name,
				"metric_key": "document_count",
				"value": document_count,
			},
		],
		status="active_value",
	)


def _execute_customer_as_of_value_artifact(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	execution_state: GovernedKpiExecutionStateContract,
	requested_scope: Dict[str, Any],
	message: str,
) -> GovernedKpiValueArtifactContract:
	customer_name = _clean_text(
		requested_scope.get("customer")
		or requested_scope.get("entity_name")
		or requested_scope.get("customer_name")
	)
	customer_label = _clean_text(
		requested_scope.get("customer_name")
		or requested_scope.get("entity_label")
		or customer_name
	)
	as_of_date = _clean_text(requested_scope.get("as_of_date")) or current_date_iso()
	company_name = _clean_text(definition_state.requested_company_name)
	execution_id = _clean_text(execution_state.execution_id)
	scalar_snapshot = get_customer_kpi_scalar_snapshot(
		customer_name,
		customer_label=customer_label,
		company=company_name,
		as_of_date=as_of_date,
	)
	receivable_snapshot = dict(scalar_snapshot.get("receivable_snapshot") or {})
	receivable_metrics = dict(receivable_snapshot.get("metrics") or {})
	policy_snapshot = dict(scalar_snapshot.get("policy_snapshot") or {})
	lifecycle_snapshot = dict(scalar_snapshot.get("lifecycle_snapshot") or {})
	threshold_state = dict(scalar_snapshot.get("credit_threshold_state") or {})
	scope = {
		"company": company_name,
		"customer": customer_name,
		"customer_name": customer_label,
	}
	if execution_id == "credit_utilization_customer_as_of_scalar_execution":
		if not bool(policy_snapshot.get("configured")):
			return build_governed_kpi_value_artifact_contract(
				execution_state=execution_state,
				entity_grain=definition_state.entity_grain,
				scope=scope,
				as_of_date=as_of_date,
				source_evidence=[{"report_name": "Customer Credit Limit"}, {"report_name": "Accounts Receivable Summary"}],
				status="blocked_missing_data",
				blocked_reason="customer credit utilization requires a configured customer credit limit for the requested company.",
			)
		outstanding_total = _numeric(receivable_metrics.get("outstanding_total"))
		credit_limit = _numeric(policy_snapshot.get("credit_limit"))
		utilization_ratio = _numeric(policy_snapshot.get("utilization_ratio"))
		return build_governed_kpi_value_artifact_contract(
			execution_state=execution_state,
			entity_grain=definition_state.entity_grain,
			scope=scope,
			as_of_date=as_of_date,
			value=utilization_ratio,
			display_value=f"{_percent(utilization_ratio)}%",
			numerator_label="Outstanding Amount",
			numerator_value=outstanding_total,
			denominator_label="Configured Credit Limit",
			denominator_value=credit_limit,
			source_evidence=[
				{"report_name": "Accounts Receivable Summary", "metric_key": "outstanding_total", "value": outstanding_total},
				{"report_name": "Customer Credit Limit", "metric_key": "credit_limit", "value": credit_limit},
			],
			threshold_state=threshold_state,
			status="active_value",
		)
	if execution_id == "customer_overdue_ratio_as_of_scalar_execution":
		outstanding_total = _numeric(receivable_metrics.get("outstanding_total"))
		overdue_total = _numeric(receivable_metrics.get("overdue_total"))
		overdue_ratio = _numeric(receivable_metrics.get("overdue_ratio"))
		return build_governed_kpi_value_artifact_contract(
			execution_state=execution_state,
			entity_grain=definition_state.entity_grain,
			scope=scope,
			as_of_date=as_of_date,
			value=overdue_ratio,
			display_value=f"{_percent(overdue_ratio)}%",
			numerator_label="31+ Aging Buckets Total",
			numerator_value=overdue_total,
			denominator_label="Outstanding Amount",
			denominator_value=outstanding_total,
			source_evidence=[
				{"report_name": "Accounts Receivable Summary", "metric_key": "overdue_total", "value": overdue_total},
				{"report_name": "Accounts Receivable Summary", "metric_key": "outstanding_total", "value": outstanding_total},
			],
			status="active_value",
		)
	if execution_id == "customer_overdue_amount_as_of_scalar_execution":
		overdue_total = _numeric(receivable_metrics.get("overdue_total"))
		outstanding_total = _numeric(receivable_metrics.get("outstanding_total"))
		return build_governed_kpi_value_artifact_contract(
			execution_state=execution_state,
			entity_grain=definition_state.entity_grain,
			scope=scope,
			as_of_date=as_of_date,
			value=overdue_total,
			display_value=f"{_money(overdue_total)} MMK",
			numerator_label="31+ Aging Buckets Total",
			numerator_value=overdue_total,
			denominator_label="Outstanding Amount",
			denominator_value=outstanding_total,
			source_evidence=[
				{"report_name": "Accounts Receivable Summary", "metric_key": "overdue_total", "value": overdue_total},
				{"report_name": "Accounts Receivable Summary", "metric_key": "outstanding_total", "value": outstanding_total},
			],
			status="active_value",
		)
	if execution_id == "customer_tenure_customer_created_at_scalar_execution":
		customer_created_date = _clean_text(lifecycle_snapshot.get("customer_created_date"))
		if not customer_created_date:
			return build_governed_kpi_value_artifact_contract(
				execution_state=execution_state,
				entity_grain=definition_state.entity_grain,
				scope=scope,
				as_of_date=as_of_date,
				source_evidence=[{"report_name": "Customer Master List"}],
				status="blocked_missing_data",
				blocked_reason="customer tenure by customer created date requires a governed customer created date.",
			)
		tenure_days = _numeric(lifecycle_snapshot.get("customer_created_tenure_days"))
		return build_governed_kpi_value_artifact_contract(
			execution_state=execution_state,
			entity_grain=definition_state.entity_grain,
			scope=scope,
			as_of_date=as_of_date,
			value=tenure_days,
			display_value=_days_text(tenure_days),
			source_evidence=[
				{"report_name": "Customer Master List", "metric_key": "customer_created_date", "value": customer_created_date},
				{"report_name": "Customer Master List", "metric_key": "as_of_date", "value": as_of_date},
			],
			status="active_value",
		)
	if execution_id == "customer_tenure_first_sales_order_scalar_execution":
		first_sales_order_date = _clean_text(lifecycle_snapshot.get("first_sales_order_date"))
		if not first_sales_order_date:
			return build_governed_kpi_value_artifact_contract(
				execution_state=execution_state,
				entity_grain=definition_state.entity_grain,
				scope=scope,
				as_of_date=as_of_date,
				source_evidence=[{"report_name": "Sales Order List"}],
				status="blocked_missing_data",
				blocked_reason="customer tenure by first sales order requires a governed first submitted sales order date.",
			)
		tenure_days = _numeric(lifecycle_snapshot.get("first_sales_order_tenure_days"))
		return build_governed_kpi_value_artifact_contract(
			execution_state=execution_state,
			entity_grain=definition_state.entity_grain,
			scope=scope,
			as_of_date=as_of_date,
			value=tenure_days,
			display_value=_days_text(tenure_days),
			source_evidence=[
				{"report_name": "Sales Order List", "metric_key": "first_sales_order_date", "value": first_sales_order_date},
				{"report_name": "Sales Order List", "metric_key": "as_of_date", "value": as_of_date},
			],
			status="active_value",
		)
	if execution_id == "customer_tenure_first_sales_invoice_scalar_execution":
		first_sales_invoice_date = _clean_text(lifecycle_snapshot.get("first_sales_invoice_date"))
		if not first_sales_invoice_date:
			return build_governed_kpi_value_artifact_contract(
				execution_state=execution_state,
				entity_grain=definition_state.entity_grain,
				scope=scope,
				as_of_date=as_of_date,
				source_evidence=[{"report_name": "Sales Invoice List"}],
				status="blocked_missing_data",
				blocked_reason="customer tenure by first sales invoice requires a governed first submitted sales invoice date.",
			)
		tenure_days = _numeric(lifecycle_snapshot.get("first_sales_invoice_tenure_days"))
		return build_governed_kpi_value_artifact_contract(
			execution_state=execution_state,
			entity_grain=definition_state.entity_grain,
			scope=scope,
			as_of_date=as_of_date,
			value=tenure_days,
			display_value=_days_text(tenure_days),
			source_evidence=[
				{"report_name": "Sales Invoice List", "metric_key": "first_sales_invoice_date", "value": first_sales_invoice_date},
				{"report_name": "Sales Invoice List", "metric_key": "as_of_date", "value": as_of_date},
			],
			status="active_value",
		)
	return build_governed_kpi_value_artifact_contract(
		execution_state=execution_state,
		entity_grain=definition_state.entity_grain,
		scope=scope,
		as_of_date=as_of_date,
		status="unsupported_execution_shape",
		blocked_reason=f"Unhandled governed customer KPI execution '{execution_id}'.",
	)


def _execute_customer_ranking_artifact(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	execution_state: GovernedKpiExecutionStateContract,
	requested_scope: Dict[str, Any],
	message: str,
) -> GovernedKpiRankingArtifactContract:
	def _customer_aging_bucket_rows(row: Dict[str, Any]) -> List[Dict[str, Any]]:
		return [
			{"bucket": "<0", "amount": _numeric(row.get("future_bucket_total"))},
			{"bucket": "0-30", "amount": _numeric(row.get("current_bucket_total"))},
			{"bucket": "31-60", "amount": _numeric(row.get("bucket_31_60_total"))},
			{"bucket": "61-90", "amount": _numeric(row.get("bucket_61_90_total"))},
			{"bucket": "91-120", "amount": _numeric(row.get("bucket_91_120_total"))},
			{"bucket": "121-Above", "amount": _numeric(row.get("bucket_121_above_total"))},
		]

	as_of_date = _clean_text(requested_scope.get("as_of_date")) or current_date_iso()
	company_name = _clean_text(definition_state.requested_company_name)
	execution_id = _clean_text(execution_state.execution_id)
	metric_aliases = _customer_metric_alias_keys(message)
	ranking_limit = int(requested_scope.get("ranking_limit") or 10)
	all_rows = list_customer_kpi_rows(company=company_name, as_of_date=as_of_date)
	selected_rows: List[Dict[str, Any]] = []
	ranking_mode = "top_n_desc"
	sort_direction = "desc"
	threshold_state: Dict[str, Any] = {}
	if execution_id == "credit_utilization_customer_as_of_ranking_execution":
		configured_rows = [row for row in all_rows if bool(row.get("credit_limit_configured"))]
		if "credit_limit_status" in metric_aliases and re.search(r"\b(above|over|exceeded)\b", _normalize_text(message)):
			ranking_mode = "threshold_match"
			threshold_state = {
				"threshold_id": "customer_credit_utilization_policy_bands",
				"matched_band_label": "limit_exceeded",
			}
			selected_rows = [
				row
				for row in configured_rows
				if _clean_text(((row.get("credit_threshold_state") or {}).get("matched_band_label"))) == "limit_exceeded"
			]
		else:
			selected_rows = sorted(
				configured_rows,
				key=lambda row: (_numeric(row.get("credit_limit_utilization_ratio")), _numeric(row.get("outstanding_total"))),
				reverse=True,
			)[:ranking_limit]
	elif execution_id == "customer_overdue_ratio_as_of_ranking_execution":
		selected_rows = sorted(
			all_rows,
			key=lambda row: (_numeric(row.get("overdue_ratio")), _numeric(row.get("overdue_total"))),
			reverse=True,
		)[:ranking_limit]
	elif execution_id == "customer_overdue_amount_as_of_ranking_execution":
		selected_rows = sorted(
			all_rows,
			key=lambda row: (_numeric(row.get("overdue_total")), _numeric(row.get("outstanding_total"))),
			reverse=True,
		)[:ranking_limit]
	else:
		return build_governed_kpi_ranking_artifact_contract(
			execution_state=execution_state,
			entity_grain=definition_state.entity_grain,
			scope={"company": company_name},
			as_of_date=as_of_date,
			status="unsupported_execution_shape",
			blocked_reason=f"Unhandled governed customer KPI ranking execution '{execution_id}'.",
		)
	if ranking_mode == "threshold_match":
		selected_rows = sorted(
			selected_rows,
			key=lambda row: (_numeric(row.get("credit_limit_excess")), _numeric(row.get("credit_limit_utilization_ratio"))),
			reverse=True,
		)
	applied_limit = ranking_limit if ranking_mode != "threshold_match" else len(selected_rows)
	if execution_id == "credit_utilization_customer_as_of_ranking_execution":
		row_payloads = [
			{
				"customer": _clean_text(row.get("customer")),
				"customer_name": _clean_text(row.get("customer_label")),
				"value": _numeric(row.get("credit_limit_utilization_ratio")),
				"display_value": f"{_percent(row.get('credit_limit_utilization_ratio'))}%",
				"outstanding_total": _numeric(row.get("outstanding_total")),
				"credit_limit": _numeric(row.get("credit_limit")),
				"credit_limit_excess": _numeric(row.get("credit_limit_excess")),
				"threshold_state": dict(row.get("credit_threshold_state") or {}),
				"aging_buckets": _customer_aging_bucket_rows(row),
			}
			for row in selected_rows
		]
	elif execution_id == "customer_overdue_ratio_as_of_ranking_execution":
		row_payloads = [
			{
				"customer": _clean_text(row.get("customer")),
				"customer_name": _clean_text(row.get("customer_label")),
				"value": _numeric(row.get("overdue_ratio")),
				"display_value": f"{_percent(row.get('overdue_ratio'))}%",
				"overdue_total": _numeric(row.get("overdue_total")),
				"outstanding_total": _numeric(row.get("outstanding_total")),
				"aging_buckets": _customer_aging_bucket_rows(row),
			}
			for row in selected_rows
		]
	else:
		row_payloads = [
			{
				"customer": _clean_text(row.get("customer")),
				"customer_name": _clean_text(row.get("customer_label")),
				"value": _numeric(row.get("overdue_total")),
				"display_value": f"{_money(row.get('overdue_total'))} MMK",
				"overdue_total": _numeric(row.get("overdue_total")),
				"outstanding_total": _numeric(row.get("outstanding_total")),
				"overdue_ratio": _numeric(row.get("overdue_ratio")),
				"aging_buckets": _customer_aging_bucket_rows(row),
			}
			for row in selected_rows
		]
	return build_governed_kpi_ranking_artifact_contract(
		execution_state=execution_state,
		entity_grain=definition_state.entity_grain,
		scope={"company": company_name},
		as_of_date=as_of_date,
		ranking_mode=ranking_mode,
		sort_direction=sort_direction,
		applied_limit=applied_limit,
		threshold_state=threshold_state,
		rows=row_payloads,
		source_evidence=[
			{"report_name": "Accounts Receivable Summary"},
			*([{"report_name": "Customer Credit Limit"}] if execution_id == "credit_utilization_customer_as_of_ranking_execution" else []),
		],
		status="active_value",
	)


def _entity_period_metric_id(execution_state: GovernedKpiExecutionStateContract) -> str:
	value_mapping = dict(execution_state.value_metric_mapping or {})
	family_metric_id = _clean_text(value_mapping.get("family_metric_id"))
	if family_metric_id:
		return family_metric_id
	value_metric = _clean_text(value_mapping.get("value_metric"))
	fallback_map = {
		"customer_revenue": "revenue",
		"customer_quantity": "quantity",
		"customer_average_order_value": "average_order_value",
		"customer_average_invoice_value": "average_invoice_value",
		"item_revenue": "revenue",
		"item_quantity": "quantity",
		"item_average_selling_price": "average_selling_price",
	}
	return fallback_map.get(value_metric, value_metric)


def _entity_period_display_label(row: Dict[str, Any], entity_grain: str) -> str:
	if entity_grain == "item":
		return (
			_clean_text(row.get("item_name"))
			or _clean_text(row.get("entity_label"))
			or _clean_text(row.get("item_code"))
			or _clean_text(row.get("entity_code"))
			or _clean_text(row.get("entity_key"))
		)
	return (
		_clean_text(row.get("customer_name"))
		or _clean_text(row.get("entity_label"))
		or _clean_text(row.get("customer"))
		or _clean_text(row.get("entity_key"))
	)


def _entity_period_join_key(entity_grain: str, row: Dict[str, Any]) -> Dict[str, Any]:
	if entity_grain == "item":
		return {"item_code": _clean_text(row.get("item_code") or row.get("entity_code") or row.get("entity_key"))}
	return {"customer": _clean_text(row.get("customer") or row.get("entity_key"))}


def _entity_period_metric_value(
	*,
	metric_id: str,
	row: Dict[str, Any],
) -> Tuple[float | None, str]:
	metric_key = _clean_text(metric_id)
	if metric_key == "revenue":
		value = _numeric(row.get("revenue_total"))
		return value, f"{_money(value)} MMK"
	if metric_key == "quantity":
		value = _numeric(row.get("quantity_total"))
		return value, f"{_count_text(value)} units"
	if metric_key in {"average_order_value", "average_invoice_value"}:
		value = _numeric(row.get("average_document_value"))
		return value, f"{_money(value)} MMK"
	if metric_key == "average_selling_price":
		value = _numeric(row.get("average_unit_price"))
		return value, f"{_money(value)} MMK"
	return None, ""


def _execute_entity_period_ranking_artifact(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	execution_state: GovernedKpiExecutionStateContract,
	requested_scope: Dict[str, Any],
) -> GovernedKpiRankingArtifactContract:
	company_name = _clean_text(definition_state.requested_company_name)
	period_start = _clean_text(requested_scope.get("period_start"))
	period_end = _clean_text(requested_scope.get("period_end"))
	ranking_limit = int(requested_scope.get("ranking_limit") or 0)
	sort_direction = _clean_text(requested_scope.get("sort_direction") or "desc").lower() or "desc"
	report_name = _clean_text((execution_state.source_reports or [""])[0])
	rows = list_entity_period_commercial_rows(
		report_name=report_name,
		company=company_name,
		from_date=period_start,
		to_date=period_end,
	)
	entity_grain = _clean_text(definition_state.entity_grain)
	metric_id = _entity_period_metric_id(execution_state)
	for row in rows:
		value, display_value = _entity_period_metric_value(metric_id=metric_id, row=row)
		row["value"] = value
		row["display_value"] = display_value
	if any(row.get("value") is None for row in rows):
		return build_governed_kpi_ranking_artifact_contract(
			execution_state=execution_state,
			entity_grain=definition_state.entity_grain,
			scope={"company": company_name},
			period_start=period_start,
			period_end=period_end,
			status="unsupported_execution_shape",
			blocked_reason=f"Unhandled governed entity period KPI execution metric '{metric_id}'.",
		)
	reverse = sort_direction != "asc"
	sorted_rows = sorted(
		rows,
		key=lambda row: (
			_numeric(row.get("value")),
			_numeric(row.get("revenue_total")),
			_entity_period_display_label(row, entity_grain),
			_clean_text(row.get("entity_code")),
		),
		reverse=reverse,
	)
	if ranking_limit > 0:
		sorted_rows = sorted_rows[:ranking_limit]
	row_payloads = [
		{
			"entity": _entity_period_display_label(row, entity_grain),
			"entity_name": _entity_period_display_label(row, entity_grain),
			"entity_key": _clean_text(row.get("entity_key")),
			"entity_code": _clean_text(row.get("entity_code")),
			"entity_grain": entity_grain,
			"customer": _clean_text(row.get("customer")),
			"customer_name": _clean_text(row.get("customer_name") or row.get("customer")),
			"item": _clean_text(row.get("item")),
			"item_code": _clean_text(row.get("item_code")),
			"item_name": _clean_text(row.get("item_name") or row.get("entity_label") or row.get("item_code")),
			"value": _numeric(row.get("value")),
			"display_value": _clean_text(row.get("display_value")),
			"revenue_total": _numeric(row.get("revenue_total")),
			"quantity_total": _numeric(row.get("quantity_total")),
			"document_count": int(_numeric(row.get("document_count"))),
			"average_document_value": _numeric(row.get("average_document_value")),
			"average_unit_price": _numeric(row.get("average_unit_price")),
			"row_provenance": [
				{
					"execution_id": execution_state.execution_id,
					"definition_id": definition_state.definition_id,
					"formula_id": formula_state.formula_id,
					"report_name": report_name,
					"metric_id": metric_id,
					"join_key": _entity_period_join_key(entity_grain, row),
				}
			],
		}
		for row in sorted_rows
	]
	return build_governed_kpi_ranking_artifact_contract(
		execution_state=execution_state,
		entity_grain=definition_state.entity_grain,
		scope={"company": company_name},
		period_start=period_start,
		period_end=period_end,
		ranking_mode="top_n_desc" if reverse else "top_n_asc",
		sort_direction="desc" if reverse else "asc",
		applied_limit=ranking_limit if ranking_limit > 0 else len(row_payloads),
		rows=row_payloads,
		source_evidence=[
			{
				"report_name": report_name,
				"period_start": period_start,
				"period_end": period_end,
			}
		],
		status="active_value",
	)


def execute_governed_kpi_artifact_from_states(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	execution_state: GovernedKpiExecutionStateContract,
	requested_scope: Dict[str, Any],
	message: str = "",
) -> Dict[str, Any]:
	execution_shape = _clean_text(execution_state.execution_shape or execution_state.requested_execution_shape)
	value_artifact = None
	ranking_artifact = None
	if execution_shape == "company_period_scalar":
		value_artifact = _execute_company_period_value_artifact(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_state=execution_state,
			requested_scope=requested_scope,
		)
	elif execution_shape == "customer_as_of_scalar":
		value_artifact = _execute_customer_as_of_value_artifact(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_state=execution_state,
			requested_scope=requested_scope,
			message=message,
		)
	elif execution_shape == "customer_as_of_ranking":
		ranking_artifact = _execute_customer_ranking_artifact(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_state=execution_state,
			requested_scope=requested_scope,
			message=message,
		)
	elif execution_shape in {"customer_period_ranking", "entity_period_ranking"}:
		ranking_artifact = _execute_entity_period_ranking_artifact(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_state=execution_state,
			requested_scope=requested_scope,
		)
	return {
		"value_artifact": value_artifact,
		"ranking_artifact": ranking_artifact,
	}


def _render_active_value_answer(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	artifact: GovernedKpiValueArtifactContract,
	requested_time_scope: str,
	include_business_purpose: bool,
	detail_requested: bool,
) -> str:
	period_phrase = f"{_period_scope_phrase(requested_time_scope)} ({artifact.period_start} to {artifact.period_end})"
	value_text = _clean_text(artifact.display_value)
	formula_basis = _formula_basis_phrase(definition_state, formula_state)
	source_report_phrase = _source_report_phrase(definition_state, formula_state)
	answer_lines = [f"For {period_phrase}, the {definition_state.label} was {value_text}."]
	if _clean_text(artifact.numerator_label) and _clean_text(artifact.denominator_label):
		if definition_state.definition_id == "collection_ratio_sales_invoice_period":
			answer_lines.append(
				f"That reflects {_money(artifact.numerator_value)} MMK collected against {_money(artifact.denominator_value)} MMK in submitted sales invoices for that period."
			)
		else:
			document_phrase = _source_documents_phrase(source_report_phrase)
			answer_lines.append(
				f"That is based on {_money(artifact.numerator_value)} MMK across {int(float(artifact.denominator_value or 0)):,} {document_phrase}."
			)
	business_purpose = _definition_business_purpose(definition_state.definition_id)
	if include_business_purpose and business_purpose:
		answer_lines.append(_sentence(f"It matters because {business_purpose}"))
	threshold_summary = _natural_threshold_summary(formula_state.formula_id)
	if threshold_summary:
		answer_lines.append(_sentence(threshold_summary))
	policy_notes = _definition_rule_notes(definition_state, formula_state)
	if detail_requested:
		answer_lines.append("")
		answer_lines.append("How it was calculated")
		if formula_basis:
			answer_lines.append(f"- Formula basis: {formula_basis}")
		if source_report_phrase:
			answer_lines.append(f"- Source: {source_report_phrase}")
		if _clean_text(artifact.numerator_label):
			answer_lines.append(f"- {_clean_text(artifact.numerator_label)}: {_money(artifact.numerator_value)} MMK")
		if _clean_text(artifact.denominator_label):
			if definition_state.definition_id == "collection_ratio_sales_invoice_period":
				denominator_text = f"{_money(artifact.denominator_value)} MMK"
			else:
				denominator_text = f"{int(float(artifact.denominator_value or 0)):,}"
			answer_lines.append(f"- {_clean_text(artifact.denominator_label)}: {denominator_text}")
		if policy_notes:
			answer_lines.append(f"- Policy: {policy_notes[0]}")
		if threshold_summary:
			answer_lines.append(f"- Threshold note: {threshold_summary.rstrip('.')}")
	return "\n".join(answer_lines).strip()


def _render_active_customer_scalar_answer(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	artifact: GovernedKpiValueArtifactContract,
	include_business_purpose: bool,
	message: str,
) -> str:
	customer_label = _clean_text(artifact.scope.get("customer_name") or artifact.scope.get("customer"))
	as_of_date = _clean_text(artifact.as_of_date)
	metric_aliases = _customer_metric_alias_keys(message)
	if artifact.status == "blocked_missing_data":
		answer_lines = [
			f"I can't calculate {definition_state.label.lower()} for {customer_label} as of {as_of_date} yet because {_clean_text(artifact.blocked_reason) or 'required ERP source data is missing'}.",
		]
		return "\n".join(answer_lines).strip()
	value_text = _clean_text(artifact.display_value)
	detail_requested = _runtime_detail_requested(message)
	if (
		definition_state.definition_id == "credit_utilization_customer_as_of_date"
		and "credit_limit_status" in metric_aliases
	):
		outstanding_total = _money(artifact.numerator_value)
		credit_limit = _money(artifact.denominator_value)
		matched_band = _clean_text((artifact.threshold_state or {}).get("matched_band_label"))
		if matched_band == "limit_exceeded":
			return (
				f"Yes. As of {as_of_date}, {customer_label} has exceeded the approved credit limit.\n\n"
				f"Current outstanding is {outstanding_total} MMK against a credit limit of {credit_limit} MMK."
			)
		return (
			f"No. As of {as_of_date}, {customer_label} is still within the approved credit limit.\n\n"
			f"Current outstanding is {outstanding_total} MMK against a credit limit of {credit_limit} MMK."
		)
	answer_lines: List[str] = []
	if definition_state.definition_id == "credit_utilization_customer_as_of_date":
		answer_lines.append(
			f"As of {as_of_date}, {customer_label} was using {value_text} of its approved credit limit."
		)
		answer_lines.append(
			f"That is {_money(artifact.numerator_value)} MMK outstanding against a credit limit of {_money(artifact.denominator_value)} MMK."
		)
	elif definition_state.definition_id == "customer_overdue_ratio_as_of_date":
		answer_lines.append(
			f"As of {as_of_date}, {customer_label} had an overdue ratio of {value_text}."
		)
		answer_lines.append(
			f"That is {_money(artifact.numerator_value)} MMK overdue out of {_money(artifact.denominator_value)} MMK outstanding."
		)
	elif definition_state.definition_id == "customer_overdue_amount_as_of_date":
		answer_lines.append(
			f"As of {as_of_date}, {customer_label} had {value_text} overdue."
		)
		answer_lines.append(
			f"That is the 31+ aging bucket total out of {_money(artifact.denominator_value)} MMK outstanding."
		)
	elif definition_state.definition_id == "customer_tenure_customer_created_at":
		customer_created_date = _source_date_value(artifact, "customer_created_date")
		answer_lines.append(
			f"As of {as_of_date}, {customer_label} had been a customer for {value_text}."
		)
		if customer_created_date:
			answer_lines.append(f"That is measured from the customer creation date of {customer_created_date}.")
	elif definition_state.definition_id == "customer_tenure_first_sales_order":
		first_sales_order_date = _source_date_value(artifact, "first_sales_order_date")
		answer_lines.append(
			f"As of {as_of_date}, {customer_label} had been trading with us for {value_text} based on the first sales order."
		)
		if first_sales_order_date:
			answer_lines.append(f"That is measured from the first submitted sales order date of {first_sales_order_date}.")
	elif definition_state.definition_id == "customer_tenure_first_sales_invoice":
		first_sales_invoice_date = _source_date_value(artifact, "first_sales_invoice_date")
		answer_lines.append(
			f"As of {as_of_date}, {customer_label} had been trading with us for {value_text} based on the first sales invoice."
		)
		if first_sales_invoice_date:
			answer_lines.append(f"That is measured from the first submitted sales invoice date of {first_sales_invoice_date}.")
	else:
		answer_lines.append(
			f"As of {as_of_date}, {customer_label} had a {definition_state.label.lower()} of {value_text}."
		)
	business_purpose = _definition_business_purpose(definition_state.definition_id)
	if include_business_purpose and business_purpose:
		answer_lines.append(_sentence(f"It matters because {business_purpose}"))
	source_report_phrase = _source_report_phrase(definition_state, formula_state)
	formula_basis = _formula_basis_phrase(definition_state, formula_state)
	if threshold_summary := _natural_threshold_summary(formula_state.formula_id, artifact_threshold_state=artifact.threshold_state):
		answer_lines.append(_sentence(threshold_summary))
	if detail_requested:
		answer_lines.append("")
		answer_lines.append("How it was calculated")
		if formula_basis:
			answer_lines.append(f"- Formula basis: {formula_basis}")
		if source_report_phrase:
			answer_lines.append(f"- Source: {source_report_phrase}")
		if _clean_text(artifact.numerator_label):
			answer_lines.append(f"- {_clean_text(artifact.numerator_label)}: {_money(artifact.numerator_value)} MMK")
		if _clean_text(artifact.denominator_label):
			answer_lines.append(f"- {_clean_text(artifact.denominator_label)}: {_money(artifact.denominator_value)} MMK")
		for evidence in artifact.source_evidence:
			report_name = _clean_text(evidence.get("report_name"))
			metric_key = _clean_text(evidence.get("metric_key"))
			value = evidence.get("value")
			if report_name and metric_key and isinstance(value, str):
				answer_lines.append(f"- {metric_key.replace('_', ' ').title()}: {value} ({report_name})")
	return "\n".join(answer_lines).strip()


def _render_active_customer_ranking_answer(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	artifact: GovernedKpiRankingArtifactContract,
	include_business_purpose: bool,
	detail_requested: bool,
) -> str:
	as_of_date = _clean_text(artifact.as_of_date)
	row_count = len(artifact.rows)
	if artifact.ranking_mode == "threshold_match" and not artifact.rows:
		answer_lines = [f"As of {as_of_date}, no customers were above the approved credit limit."]
	elif artifact.ranking_mode == "threshold_match":
		answer_lines = [f"As of {as_of_date}, {row_count} customers were above the approved credit limit."]
	else:
		answer_lines = [f"As of {as_of_date}, here are the top {int(max(1, artifact.applied_limit))} customers by {definition_state.label.lower()}."]
	business_purpose = _definition_business_purpose(definition_state.definition_id)
	if include_business_purpose and business_purpose:
		answer_lines.append(_sentence(f"It matters because {business_purpose}"))
	if not artifact.rows:
		if artifact.ranking_mode != "threshold_match":
			answer_lines.append("No customers matched the current ranking criteria.")
	else:
		for index, row in enumerate(artifact.rows, start=1):
			customer_label = _clean_text(row.get("customer_name") or row.get("customer"))
			display_value = _clean_text(row.get("display_value"))
			if artifact.execution_id == "credit_utilization_customer_as_of_ranking_execution":
				credit_limit = _money(row.get("credit_limit"))
				outstanding = _money(row.get("outstanding_total"))
				if artifact.ranking_mode == "threshold_match":
					excess = _money(row.get("credit_limit_excess"))
					answer_lines.append(
						f"- {index}. {customer_label}: {display_value} used, {excess} MMK above limit "
						f"(Outstanding {_money(row.get('outstanding_total'))} MMK; Credit Limit {credit_limit} MMK)"
					)
				else:
					answer_lines.append(
						f"- {index}. {customer_label}: {display_value} used "
						f"(Outstanding {outstanding} MMK; Credit Limit {credit_limit} MMK)"
					)
			elif artifact.execution_id == "customer_overdue_amount_as_of_ranking_execution":
				answer_lines.append(
					f"- {index}. {customer_label}: {display_value} overdue "
					f"(Outstanding {_money(row.get('outstanding_total'))} MMK; Overdue Ratio {_percent(row.get('overdue_ratio'))}%)"
				)
			else:
				answer_lines.append(
					f"- {index}. {customer_label}: {display_value} overdue ratio "
					f"(Overdue {_money(row.get('overdue_total'))} MMK; Outstanding {_money(row.get('outstanding_total'))} MMK)"
				)
	if detail_requested:
		formula_basis = _formula_basis_phrase(definition_state, formula_state)
		source_report_phrase = _source_report_phrase(definition_state, formula_state)
		answer_lines.append("")
		answer_lines.append("How it was ranked")
		if formula_basis:
			answer_lines.append(f"- Formula basis: {formula_basis}")
		if source_report_phrase:
			answer_lines.append(f"- Source: {source_report_phrase}")
		if artifact.ranking_mode == "threshold_match":
			matched_band = _clean_text(artifact.threshold_state.get("matched_band_label"))
			if matched_band:
				answer_lines.append(f"- Threshold filter: {matched_band}")
	return "\n".join(answer_lines).strip()


def _render_active_entity_period_ranking_answer(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	artifact: GovernedKpiRankingArtifactContract,
	requested_time_scope: str,
	include_business_purpose: bool,
	detail_requested: bool,
) -> str:
	period_phrase = f"{_period_scope_phrase(requested_time_scope)} ({artifact.period_start} to {artifact.period_end})"
	entity_grain = _clean_text(definition_state.entity_grain or artifact.entity_grain)
	entity_label = "products" if entity_grain == "item" else "customers"
	primary_noun = "revenue"
	if definition_state.definition_id.endswith("_quantity_period"):
		primary_noun = "quantity"
	elif "average_order_value" in definition_state.definition_id:
		primary_noun = "average order value"
	elif "average_invoice_value" in definition_state.definition_id:
		primary_noun = "average invoice value"
	elif "average_selling_price" in definition_state.definition_id:
		primary_noun = "average selling price"
	source_phrase = _source_report_phrase(definition_state, formula_state)
	basis_phrase = _source_documents_phrase(source_phrase)
	answer_lines = [
		f"For {period_phrase}, here are the top {int(max(1, artifact.applied_limit))} {entity_label} by {primary_noun} based on {basis_phrase}."
	]
	business_purpose = _definition_business_purpose(definition_state.definition_id)
	if include_business_purpose and business_purpose:
		answer_lines.append(_sentence(f"It matters because {business_purpose}"))
	if not artifact.rows:
		answer_lines.append(f"No {entity_label} matched the current ranking scope.")
	else:
		for index, row in enumerate(artifact.rows, start=1):
			entity_name = (
				_clean_text(row.get("entity_name"))
				or _clean_text(row.get("item_name"))
				or _clean_text(row.get("customer_name"))
				or _clean_text(row.get("item_code"))
				or _clean_text(row.get("customer"))
			)
			answer_lines.append(
				f"- {index}. {entity_name}: {_clean_text(row.get('display_value'))}"
			)
	if detail_requested:
		formula_basis = _formula_basis_phrase(definition_state, formula_state)
		source_report_phrase = _source_report_phrase(definition_state, formula_state)
		answer_lines.append("")
		answer_lines.append("How it was ranked")
		if formula_basis:
			answer_lines.append(f"- Formula basis: {formula_basis}")
		if source_report_phrase:
			answer_lines.append(f"- Source: {source_report_phrase}")
	return "\n".join(answer_lines).strip()


def _render_ambiguous_value_answer(
	*,
	definition_state: BusinessDefinitionStateContract,
	requested_time_scope: str,
) -> str:
	lookup_value = _clean_text(definition_state.lookup_value) or "this KPI"
	options = [
		_clean_text(item.get("label"))
		for item in definition_state.candidate_definitions
		if _clean_text(item.get("label"))
	]
	if requested_time_scope:
		start_date, end_date = _date_range_from_time_scope(requested_time_scope)
		return render_shared_choice_list_clarification(
			reason_type="governed_kpi_definition_ambiguity",
			variant="kpi_value_with_period",
			template_values={
				"lookup_label": lookup_value,
				"period_phrase": _period_scope_phrase(requested_time_scope),
				"period_start": start_date,
				"period_end": end_date,
			},
			options=options,
			default_question=(
				f"I can calculate {lookup_value} for {_period_scope_phrase(requested_time_scope)} "
				f"({start_date} to {end_date}), but I need the approved basis first."
			),
		)
	return render_shared_choice_list_clarification(
		reason_type="governed_kpi_definition_ambiguity",
		variant="kpi_value_default",
		template_values={
			"lookup_label": lookup_value,
		},
		options=options,
		default_question=f"I can calculate {lookup_value}, but I need the approved basis first.",
	)


def _render_missing_period_answer(
	*,
	definition_state: BusinessDefinitionStateContract,
) -> str:
	return render_shared_choice_list_clarification(
		reason_type="time_scope_missing",
		variant="kpi_value_period_missing",
		template_values={
			"lookup_label": _clean_text(definition_state.label) or "this KPI",
		},
		options=_period_scope_options(),
		default_question=f"I can calculate {definition_state.label}, but I still need the business period.",
	)


def _execution_continuation_message(
	*,
	lookup_term: str,
	requested_time_scope: str = "",
	continuation_suffix: str = "",
) -> str:
	base = f"show {_clean_text(lookup_term)}".strip()
	if requested_time_scope:
		base = f"{base} {_period_scope_phrase(requested_time_scope)}"
	if _clean_text(continuation_suffix):
		base = f"{base} {_clean_text(continuation_suffix)}"
	return base.strip()


def _build_ambiguous_execution_clarification_signal(
	*,
	request_id: str,
	definition_state: BusinessDefinitionStateContract,
	answer_text: str,
	requested_time_scope: str,
	continuation_suffix: str = "",
) -> Dict[str, Any]:
	def _definition_option_aliases(definition_id: str, label: str) -> List[str]:
		aliases: List[str] = []
		label_text = _clean_text(label)
		label_parts = re.split(r"\s+by\s+", label_text, flags=re.IGNORECASE, maxsplit=1)
		if len(label_parts) == 2:
			label_suffix = _clean_text(label_parts[1])
			aliases.append(label_suffix.lower())
			aliases.append(label_suffix)
		for item in list_business_definition_specs():
			if _clean_text(item.get("definition_id")) != _clean_text(definition_id):
				continue
			for raw_term in (item.get("lookup_terms") or []):
				clean_term = _clean_text(raw_term)
				if clean_term:
					aliases.append(clean_term)
			break
		listing_view_canonical = _definition_listing_view_canonical(definition_id)
		aliases.extend(_listing_view_aliases_for_canonical(listing_view_canonical))
		seen: set[str] = set()
		unique_aliases: List[str] = []
		for alias in aliases:
			normalized = _normalize_text(alias)
			if not normalized or normalized in seen or normalized == _normalize_text(label):
				continue
			seen.add(normalized)
			unique_aliases.append(alias)
		return unique_aliases

	options = [
		_clean_text(item.get("label"))
		for item in (definition_state.candidate_definitions or [])
		if isinstance(item, dict) and _clean_text(item.get("label"))
	]
	if not options:
		return {}
	resolved_message_by_option: Dict[str, str] = {}
	option_aliases_by_option: Dict[str, List[str]] = {}
	semantic_slot_value_by_option: Dict[str, str] = {}
	for item in (definition_state.candidate_definitions or []):
		if not isinstance(item, dict):
			continue
		label = _clean_text(item.get("label"))
		definition_id = _clean_text(item.get("definition_id"))
		if not label or not definition_id:
			continue
		resolved_message_by_option[label] = _execution_continuation_message(
			lookup_term=_specific_lookup_term_for_definition(
				definition_id=definition_id,
				fallback_label=label,
				ambiguous_lookup_value=_clean_text(definition_state.lookup_value),
			),
			requested_time_scope=requested_time_scope,
			continuation_suffix=continuation_suffix,
		)
		option_aliases = _definition_option_aliases(definition_id, label)
		if option_aliases:
			option_aliases_by_option[label] = option_aliases
		listing_view_canonical = _definition_listing_view_canonical(definition_id)
		if listing_view_canonical:
			semantic_slot_value_by_option[label] = listing_view_canonical
	carryover_slot_values = {
		"lookup_value": _clean_text(definition_state.lookup_value),
		"requested_time_scope": _clean_text(requested_time_scope),
	}
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="frontdoor",
		reason_type="governed_kpi_definition_ambiguity",
		user_question=answer_text,
		suggested_options=options,
		internal_reason="The governed KPI runtime request maps to multiple approved KPI definitions and must be clarified before execution.",
		internal_details={
			"continuation_lane": "front_door",
			"continuation_intent_class": "governed_kpi_value",
			"clarification_template_group": "shared_clarification",
			"resolved_message_by_option": resolved_message_by_option,
			"option_aliases_by_option": option_aliases_by_option,
			"semantic_slot_name": "listing_view" if semantic_slot_value_by_option else "",
			"semantic_slot_value_by_option": semantic_slot_value_by_option,
			"carryover_slot_values": {
				key: value
				for key, value in carryover_slot_values.items()
				if _clean_text(value)
			},
			"requested_time_scope": requested_time_scope,
			"candidate_definition_ids": [
				_clean_text(item.get("definition_id"))
				for item in (definition_state.candidate_definitions or [])
				if isinstance(item, dict) and _clean_text(item.get("definition_id"))
			],
		},
	).to_payload()


def _build_missing_period_clarification_signal(
	*,
	request_id: str,
	definition_state: BusinessDefinitionStateContract,
	answer_text: str,
) -> Dict[str, Any]:
	options = _period_scope_options()
	listing_view = _definition_listing_view_canonical(_clean_text(definition_state.definition_id))
	resolved_message_by_option = {
		option: _execution_continuation_message(
			lookup_term=definition_state.lookup_value or definition_state.label,
			requested_time_scope=_PERIOD_SCOPE_ORDER[idx],
		)
		for idx, option in enumerate(options)
	}
	carryover_slot_values = {
		"lookup_value": _clean_text(definition_state.lookup_value or definition_state.label),
		"listing_view": listing_view,
	}
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="frontdoor",
		reason_type="time_scope_missing",
		user_question=answer_text,
		suggested_options=options,
		internal_reason="The governed KPI runtime request requires an explicit business period before execution can proceed.",
		internal_details={
			"continuation_lane": "front_door",
			"continuation_intent_class": "governed_kpi_value",
			"clarification_template_group": "shared_clarification",
			"resolved_message_by_option": resolved_message_by_option,
			"carryover_slot_values": {
				key: value
				for key, value in carryover_slot_values.items()
				if _clean_text(value)
			},
			"suggested_time_scope_options": options,
		},
	).to_payload()


def maybe_build_governed_kpi_value_frontdoor_response(
	*,
	request_id: str,
	message: str,
	company_name: str = "",
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	raw_message = _clean_text(message)
	if not raw_message:
		return {}
	include_business_purpose = _business_purpose_requested(raw_message)
	normalized_message = _with_business_purpose_suffix_removed(raw_message)
	resolved_company_name = _current_company_name(company_name)
	requested_time_scope = _extract_period_time_scope(normalized_message)
	definition_state: BusinessDefinitionStateContract | None = None
	formula_state: GovernedFormulaStateContract | None = None
	execution_state: GovernedKpiExecutionStateContract | None = None
	requested_scope: Dict[str, Any] = {}
	execution_shape = ""
	is_customer_ranking_request = _looks_like_customer_ranking_request(normalized_message)
	if period_definition_state := _resolve_definition_state_from_message_match(
		message=normalized_message,
		company_name=resolved_company_name,
	):
		if _looks_like_runtime_value_request(
			normalized_message,
			requested_time_scope=requested_time_scope,
			definition_state=period_definition_state,
		):
			definition_state = period_definition_state
			formula_state = resolve_governed_formula_state(
				definition_state=definition_state,
				company_name=resolved_company_name,
			)
			requested_scope = _build_period_requested_scope(requested_time_scope)
			if _clean_text(definition_state.entity_grain) == "customer" and is_customer_ranking_request:
				requested_scope["ranking_limit"] = _requested_top_n(normalized_message, default_limit=10)
				execution_shape = "entity_period_ranking"
			else:
				execution_shape = "company_period_scalar"
			execution_state = resolve_governed_kpi_execution_state(
				definition_state=definition_state,
				formula_state=formula_state,
				execution_shape=execution_shape,
				company_name=resolved_company_name,
				requested_scope=requested_scope,
			)
	if definition_state is None:
		customer_definition_state = _resolve_customer_definition_state_from_message(
			message=normalized_message,
			company_name=resolved_company_name,
			is_ranking_request=is_customer_ranking_request,
		)
		if customer_definition_state is None:
			return {}
		if not _looks_like_customer_runtime_value_request(
			normalized_message,
			is_ranking_request=is_customer_ranking_request,
		):
			return {}
		definition_state = customer_definition_state
		formula_state = resolve_governed_formula_state(
			definition_state=definition_state,
			company_name=resolved_company_name,
		)
		requested_scope = _build_customer_requested_scope(
			normalized_message,
			grounded_turn=grounded_turn,
		)
		execution_shape = _customer_execution_shape(normalized_message)
		execution_state = resolve_governed_kpi_execution_state(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_shape=execution_shape,
			company_name=resolved_company_name,
			requested_scope=requested_scope,
		)
	if definition_state is None or formula_state is None or execution_state is None:
		return {}
	clarification_signal_payload: Dict[str, Any] = {}
	artifact = None
	ranking_artifact = None
	if definition_state.resolution_state == "ambiguous" or execution_state.resolution_state == "clarify_basis":
		answer_text = _render_ambiguous_value_answer(
			definition_state=definition_state,
			requested_time_scope=requested_time_scope,
		)
		clarification_signal_payload = _build_ambiguous_execution_clarification_signal(
			request_id=request_id,
			definition_state=definition_state,
			answer_text=answer_text,
			requested_time_scope=requested_time_scope,
			continuation_suffix=_customer_continuation_suffix(requested_scope),
		)
	elif execution_state.resolution_state == "clarify_scope":
		if execution_shape == "company_period_scalar":
			answer_text = _render_missing_period_answer(definition_state=definition_state)
			clarification_signal_payload = _build_missing_period_clarification_signal(
				request_id=request_id,
				definition_state=definition_state,
				answer_text=answer_text,
			)
		else:
			answer_text = _render_missing_customer_answer(
				definition_state=definition_state,
				as_of_date=_clean_text(requested_scope.get("as_of_date")) or current_date_iso(),
			)
			clarification_signal_payload = _build_missing_customer_clarification_signal(
				request_id=request_id,
				definition_state=definition_state,
				as_of_date=_clean_text(requested_scope.get("as_of_date")) or current_date_iso(),
				answer_text=answer_text,
			)
	elif execution_state.resolution_state == "active_value":
		execution_payload = execute_governed_kpi_artifact_from_states(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_state=execution_state,
			requested_scope=requested_scope,
			message=normalized_message,
		)
		artifact = execution_payload.get("value_artifact")
		ranking_artifact = execution_payload.get("ranking_artifact")
		if execution_shape == "company_period_scalar" and artifact is not None:
			answer_text = _render_active_value_answer(
				definition_state=definition_state,
				formula_state=formula_state,
				artifact=artifact,
				requested_time_scope=requested_time_scope,
				include_business_purpose=include_business_purpose,
				detail_requested=_runtime_detail_requested(normalized_message),
			)
		elif execution_shape == "customer_as_of_scalar" and artifact is not None:
			answer_text = _render_active_customer_scalar_answer(
				definition_state=definition_state,
				formula_state=formula_state,
				artifact=artifact,
				include_business_purpose=include_business_purpose,
				message=normalized_message,
			)
		elif execution_shape == "customer_as_of_ranking" and ranking_artifact is not None:
			answer_text = _render_active_customer_ranking_answer(
				definition_state=definition_state,
				formula_state=formula_state,
				artifact=ranking_artifact,
				include_business_purpose=include_business_purpose,
				detail_requested=_runtime_detail_requested(normalized_message),
			)
		elif execution_shape in {"customer_period_ranking", "entity_period_ranking"} and ranking_artifact is not None:
			answer_text = _render_active_entity_period_ranking_answer(
				definition_state=definition_state,
				formula_state=formula_state,
				artifact=ranking_artifact,
				requested_time_scope=requested_time_scope,
				include_business_purpose=include_business_purpose,
				detail_requested=_runtime_detail_requested(normalized_message),
			)
		else:
			return {}
	else:
		return {}
	intent_spec = get_frontdoor_intent_spec("governed_kpi_value")
	if not intent_spec:
		intent_spec = {
			"intent_class_id": "governed_kpi_value",
			"response_mode": "direct_answer",
			"route_target": "front_door",
			"handle_in_front_door": True,
		}
	reason = (
		f"The turn is a governed KPI value request for '{definition_state.label or definition_state.lookup_value}', "
		"so it should be answered from the approved KPI execution registry."
	)
	semantic_result = SemanticFrontDoorResult(
		status="accepted",
		intent=SemanticFrontDoorIntent(
			intent_class="governed_kpi_value",
			confidence=1.0,
			reason=reason,
		),
		confidence_threshold=1.0,
	)
	frontdoor_contract = FrontDoorIntentGateContract(
		request_id=_clean_text(request_id),
		intent_class="governed_kpi_value",
		confidence=1.0,
		handle_in_front_door=bool(intent_spec.get("handle_in_front_door", True)),
		response_mode=_clean_text(intent_spec.get("response_mode") or "direct_answer") or "direct_answer",
		response_payload={
			"text": answer_text,
			"company_name": resolved_company_name,
			"lookup_value": _clean_text(definition_state.lookup_value),
			"requested_time_scope": requested_time_scope,
			"period_start": _clean_text(requested_scope.get("period_start")),
			"period_end": _clean_text(requested_scope.get("period_end")),
			"as_of_date": _clean_text(requested_scope.get("as_of_date")),
			"definition_state": definition_state.to_payload(),
			"formula_state": formula_state.to_payload(),
			"execution_state": execution_state.to_payload(),
			"kpi_value_artifact": artifact.to_payload() if artifact is not None else {},
			"kpi_ranking_artifact": ranking_artifact.to_payload() if ranking_artifact is not None else {},
			"clarification_signal_payload": clarification_signal_payload,
		},
		route_target=_clean_text(intent_spec.get("route_target") or "front_door") or "front_door",
		reason=reason,
	)
	return {
		"semantic_result": semantic_result,
		"frontdoor_contract": frontdoor_contract,
		"frontdoor_answer": answer_text,
		"definition_state": definition_state.to_payload(),
		"formula_state": formula_state.to_payload(),
		"execution_state": execution_state.to_payload(),
		"kpi_value_artifact": artifact.to_payload() if artifact is not None else {},
		"kpi_ranking_artifact": ranking_artifact.to_payload() if ranking_artifact is not None else {},
		"clarification_signal_payload": clarification_signal_payload,
	}


def governed_kpi_value_frontdoor_candidate_available(
	*,
	message: str,
	company_name: str = "",
	grounded_turn: Dict[str, Any] | None = None,
) -> bool:
	"""
	Return whether the governed KPI front door can own this turn.

	This is intentionally a lightweight ownership check: it uses the same
	definition/execution registry resolution as the renderer path, but it does
	not execute KPI data reads or render an answer.
	"""
	raw_message = _clean_text(message)
	if not raw_message:
		return False
	normalized_message = _with_business_purpose_suffix_removed(raw_message)
	resolved_company_name = _current_company_name(company_name)
	requested_time_scope = _extract_period_time_scope(normalized_message)
	is_customer_ranking_request = _looks_like_customer_ranking_request(normalized_message)
	if period_definition_state := _resolve_definition_state_from_message_match(
		message=normalized_message,
		company_name=resolved_company_name,
	):
		if _looks_like_runtime_value_request(
			normalized_message,
			requested_time_scope=requested_time_scope,
			definition_state=period_definition_state,
		):
			return True
	customer_definition_state = _resolve_customer_definition_state_from_message(
		message=normalized_message,
		company_name=resolved_company_name,
		is_ranking_request=is_customer_ranking_request,
	)
	if customer_definition_state is None:
		return False
	return _looks_like_customer_runtime_value_request(
		normalized_message,
		is_ranking_request=is_customer_ranking_request,
	)


def _probe_safe_response(payload: Dict[str, Any]) -> Dict[str, Any]:
	if not isinstance(payload, dict):
		return {}
	out = dict(payload)
	semantic_result = out.get("semantic_result")
	if semantic_result is not None and hasattr(semantic_result, "to_payload"):
		out["semantic_result"] = semantic_result.to_payload()
	frontdoor_contract = out.get("frontdoor_contract")
	if frontdoor_contract is not None and hasattr(frontdoor_contract, "to_payload"):
		out["frontdoor_contract"] = frontdoor_contract.to_payload()
	return out


def run_governed_kpi_period_execution_probe() -> Dict[str, Any]:
	company_name = "Mingalar Mobile Distribution Co., Ltd."
	aov_value = maybe_build_governed_kpi_value_frontdoor_response(
		request_id="phase2-5b-aov",
		message="what is average order value for sales orders last month",
		company_name=company_name,
	)
	ambiguous = maybe_build_governed_kpi_value_frontdoor_response(
		request_id="phase2-5b-ambiguous",
		message="show average order value last month",
		company_name=company_name,
	)
	clarify_period = maybe_build_governed_kpi_value_frontdoor_response(
		request_id="phase2-5b-period",
		message="what is average order value for sales orders",
		company_name=company_name,
	)
	collection_ratio = maybe_build_governed_kpi_value_frontdoor_response(
		request_id="phase2-5b-collection",
		message="show collection ratio last month",
		company_name=company_name,
	)
	ok = (
		_clean_text(((aov_value.get("execution_state") or {}).get("resolution_state") if isinstance(aov_value, dict) else "")) == "active_value"
		and _clean_text((((aov_value.get("kpi_value_artifact") or {}).get("display_value")) if isinstance(aov_value, dict) else ""))
		and _clean_text(((ambiguous.get("definition_state") or {}).get("resolution_state") if isinstance(ambiguous, dict) else "")) == "ambiguous"
		and _clean_text((((ambiguous.get("clarification_signal_payload") or {}).get("reason_type")) if isinstance(ambiguous, dict) else "")) == "governed_kpi_definition_ambiguity"
		and _clean_text(((clarify_period.get("execution_state") or {}).get("resolution_state") if isinstance(clarify_period, dict) else "")) == "clarify_scope"
		and _clean_text((((clarify_period.get("clarification_signal_payload") or {}).get("reason_type")) if isinstance(clarify_period, dict) else "")) == "time_scope_missing"
		and _clean_text(((collection_ratio.get("execution_state") or {}).get("resolution_state") if isinstance(collection_ratio, dict) else "")) == "active_value"
	)
	return {
		"ok": ok,
		"aov_value": _probe_safe_response(aov_value),
		"ambiguous": _probe_safe_response(ambiguous),
		"clarify_period": _probe_safe_response(clarify_period),
		"collection_ratio": _probe_safe_response(collection_ratio),
	}


def run_governed_kpi_customer_execution_probe() -> Dict[str, Any]:
	company_name = "Mingalar Mobile Distribution Co., Ltd."
	credit_utilization = maybe_build_governed_kpi_value_frontdoor_response(
		request_id="phase2-5c-credit-utilization",
		message="what is customer credit utilization for Zegyo Mobile Supply House as of today",
		company_name=company_name,
	)
	overdue_ratio = maybe_build_governed_kpi_value_frontdoor_response(
		request_id="phase2-5c-overdue-ratio",
		message="what is customer overdue ratio for Zegyo Mobile Supply House as of today",
		company_name=company_name,
	)
	tenure_missing_customer = maybe_build_governed_kpi_value_frontdoor_response(
		request_id="phase2-5c-tenure-missing-customer",
		message="show customer tenure by first sales order as of today",
		company_name=company_name,
	)
	ranking = maybe_build_governed_kpi_value_frontdoor_response(
		request_id="phase2-5c-ranking",
		message="show top 5 customers by credit utilization as of today",
		company_name=company_name,
	)
	above_limit = maybe_build_governed_kpi_value_frontdoor_response(
		request_id="phase2-5c-above-limit",
		message="show customers above credit limit",
		company_name=company_name,
	)
	deictic_tenure = maybe_build_governed_kpi_value_frontdoor_response(
		request_id="phase2-5c-deictic-tenure",
		message="what is this customer's tenure by customer created date?",
		company_name=company_name,
		grounded_turn={
			"artifact_family_id": "entity_detail",
			"known_entities": [
				{
					"entity_type": "customer",
					"name": "Zegyo Mobile Supply House",
					"code": "Zegyo Mobile Supply House",
				}
			],
			"filters": {
				"entity_type": "customer",
				"entity_key": "Zegyo Mobile Supply House",
			},
		},
	)
	ok = (
		_clean_text(((credit_utilization.get("execution_state") or {}).get("resolution_state") if isinstance(credit_utilization, dict) else "")) == "active_value"
		and _clean_text((((credit_utilization.get("kpi_value_artifact") or {}).get("display_value")) if isinstance(credit_utilization, dict) else ""))
		and _clean_text(((overdue_ratio.get("execution_state") or {}).get("resolution_state") if isinstance(overdue_ratio, dict) else "")) == "active_value"
		and _clean_text(((tenure_missing_customer.get("execution_state") or {}).get("resolution_state") if isinstance(tenure_missing_customer, dict) else "")) == "clarify_scope"
		and _clean_text((((tenure_missing_customer.get("clarification_signal_payload") or {}).get("reason_type")) if isinstance(tenure_missing_customer, dict) else "")) == "customer_scope_missing"
		and _clean_text(((ranking.get("execution_state") or {}).get("resolution_state") if isinstance(ranking, dict) else "")) == "active_value"
		and isinstance((ranking.get("kpi_ranking_artifact") or {}).get("rows"), list)
		and len((ranking.get("kpi_ranking_artifact") or {}).get("rows") or []) > 0
		and _clean_text(((above_limit.get("execution_state") or {}).get("resolution_state") if isinstance(above_limit, dict) else "")) == "active_value"
		and _clean_text(((deictic_tenure.get("execution_state") or {}).get("resolution_state") if isinstance(deictic_tenure, dict) else "")) == "active_value"
	)
	return {
		"ok": ok,
		"credit_utilization": _probe_safe_response(credit_utilization),
		"overdue_ratio": _probe_safe_response(overdue_ratio),
		"tenure_missing_customer": _probe_safe_response(tenure_missing_customer),
		"ranking": _probe_safe_response(ranking),
		"above_limit": _probe_safe_response(above_limit),
		"deictic_tenure": _probe_safe_response(deictic_tenure),
	}
