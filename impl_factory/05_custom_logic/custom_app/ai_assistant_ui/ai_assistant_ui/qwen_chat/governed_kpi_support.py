from __future__ import annotations

import re
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.business_definition_state import (
	BusinessDefinitionStateContract,
	GovernedFormulaStateContract,
	build_governed_formula_state_contract,
	resolve_business_definition_state,
	resolve_governed_formula_state,
)
from ai_assistant_ui.qwen_chat.contracts import (
	FrontDoorIntentGateContract,
	build_clarification_signal_contract,
)
from ai_assistant_ui.qwen_chat.defaults_repository import single_company_name
from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import (
	SemanticFrontDoorIntent,
	SemanticFrontDoorResult,
)
from ai_assistant_ui.qwen_chat.metadata import (
	get_frontdoor_intent_spec,
	list_business_definition_specs,
	list_business_rule_specs,
	list_business_threshold_specs_for_formula,
)


_EXPLICIT_KPI_DEFINITION_PATTERNS = (
	("define", re.compile(r"^(?:please\s+)?(?:can you\s+)?define\s+(?P<subject>.+?)\??$", re.IGNORECASE)),
	("meaning", re.compile(r"^(?:please\s+)?(?:can you\s+)?what does\s+(?P<subject>.+?)\s+mean(?:\s+in\s+this\s+erp)?\??$", re.IGNORECASE)),
	("formula", re.compile(r"^(?:please\s+)?(?:can you\s+)?what is the formula for\s+(?P<subject>.+?)\??$", re.IGNORECASE)),
	("formula", re.compile(r"^(?:please\s+)?(?:can you\s+)?tell me the formula for\s+(?P<subject>.+?)\??$", re.IGNORECASE)),
	("formula", re.compile(r"^(?:please\s+)?formula for\s+(?P<subject>.+?)\??$", re.IGNORECASE)),
	("calculation", re.compile(r"^(?:please\s+)?(?:can you\s+)?how do you calculate\s+(?P<subject>.+?)\??$", re.IGNORECASE)),
	("calculation", re.compile(r"^(?:please\s+)?(?:can you\s+)?how is\s+(?P<subject>.+?)\s+calculated\??$", re.IGNORECASE)),
)
_BARE_WHAT_IS_PATTERN = re.compile(r"^(?:please\s+)?(?:can you\s+)?what is\s+(?P<subject>.+?)\??$", re.IGNORECASE)
_DEICTIC_OR_CONTEXTUAL_PATTERN = re.compile(r"\b(this|that|these|those|my|our|your|current|latest)\b", re.IGNORECASE)
_DYNAMIC_TIME_SCOPE_PATTERN = re.compile(
	r"\b("
	r"today|yesterday|tomorrow|"
	r"(?:last|this|next)\s+(?:week|month|quarter|year)|"
	r"between|"
	r"from\s+.+\s+to|"
	r"as of\s+(?:today|yesterday|tomorrow|\d{4}-\d{2}-\d{2})|"
	r"\d{4}-\d{2}-\d{2}"
	r")\b",
	re.IGNORECASE,
)
_ALLOWED_UNDEFINED_QUERY_KINDS = {"define", "meaning", "formula", "calculation"}
_BUSINESS_PURPOSE_SUFFIX_PATTERN = re.compile(r"\s+and\s+why\s+does\s+it\s+matter$", re.IGNORECASE)
_ERP_CONTEXT_SUFFIX_PATTERN = re.compile(r"\s+in\s+this\s+erp$", re.IGNORECASE)


def _clean_subject(value: Any) -> str:
	text = str(value or "").strip()
	if not text:
		return ""
	text = re.sub(r"\s+", " ", text)
	return text.strip(" .?!")


def _normalize_extracted_subject(subject: str) -> Dict[str, Any]:
	clean_subject = _clean_subject(subject)
	if not clean_subject:
		return {}
	include_business_purpose = bool(_BUSINESS_PURPOSE_SUFFIX_PATTERN.search(clean_subject))
	base_subject = _BUSINESS_PURPOSE_SUFFIX_PATTERN.sub("", clean_subject)
	base_subject = _ERP_CONTEXT_SUFFIX_PATTERN.sub("", base_subject)
	base_subject = _clean_subject(base_subject)
	if not base_subject:
		return {}
	return {
		"subject": base_subject,
		"include_business_purpose": include_business_purpose,
	}


def _extract_definition_subject(message: str) -> Dict[str, Any]:
	text = str(message or "").strip()
	if not text:
		return {}
	for query_kind, pattern in _EXPLICIT_KPI_DEFINITION_PATTERNS:
		match = pattern.match(text)
		if match:
			normalized = _normalize_extracted_subject(match.group("subject"))
			if normalized:
				return {"query_kind": query_kind, **normalized}
	bare_match = _BARE_WHAT_IS_PATTERN.match(text)
	if not bare_match:
		return {}
	normalized = _normalize_extracted_subject(bare_match.group("subject"))
	if not normalized:
		return {}
	return {"query_kind": "bare_what_is", **normalized}


def _subject_is_dynamic_or_deictic(subject: str) -> bool:
	text = str(subject or "").strip()
	if not text:
		return True
	return bool(_DEICTIC_OR_CONTEXTUAL_PATTERN.search(text) or _DYNAMIC_TIME_SCOPE_PATTERN.search(text))


def _normalize_phrase(value: Any) -> str:
	text = str(value or "").strip().lower()
	text = re.sub(r"[_-]+", " ", text)
	text = re.sub(r"\s+", " ", text)
	return text.strip()


def _company_scope_matches(values: Any, company_name: str) -> bool:
	scope_values = [
		_normalize_phrase(item)
		for item in (values or [])
		if _normalize_phrase(item)
	]
	if not scope_values:
		return True
	normalized_company = _normalize_phrase(company_name)
	return not normalized_company or normalized_company in scope_values or "global" in scope_values


def _current_company_name(explicit_company_name: str) -> str:
	company_name = str(explicit_company_name or "").strip()
	if company_name:
		return company_name
	return single_company_name()


def _format_title_case_token(value: Any) -> str:
	text = str(value or "").strip()
	if not text:
		return ""
	text = text.replace("_", " ")
	text = re.sub(r"\s+", " ", text)
	return text.title()


def _format_governed_phrase(value: Any) -> str:
	text = str(value or "").strip().lower()
	phrase_map = {
		"as_of_date": "As of date",
		"transaction_period": "Transaction period",
		"first_sales_order_date": "First sales order date",
		"first_sales_invoice_date": "First sales invoice date",
		"customer_created_at": "Customer created date",
		"latest_value": "Latest value",
		"ratio_of_sums": "Ratio of sums",
	}
	if text in phrase_map:
		return phrase_map[text]
	return _format_title_case_token(value)


def _lower_first(text: str) -> str:
	value = str(text or "").strip()
	if not value:
		return ""
	return value[:1].lower() + value[1:]


def _join_clean(values: List[str]) -> str:
	items = [str(value or "").strip() for value in (values or []) if str(value or "").strip()]
	if not items:
		return ""
	if len(items) == 1:
		return items[0]
	if len(items) == 2:
		return f"{items[0]} and {items[1]}"
	return ", ".join(items[:-1]) + f", and {items[-1]}"


def _generic_kpi_examples() -> List[str]:
	examples: List[str] = []
	for item in list_business_definition_specs():
		lookup_terms = item.get("lookup_terms") if isinstance(item.get("lookup_terms"), list) else []
		term = str(lookup_terms[0] or "").strip() if lookup_terms else ""
		if term and term not in examples:
			examples.append(term)
	return examples[:5]


def _definition_description(definition_id: str) -> str:
	for item in list_business_definition_specs():
		if str(item.get("definition_id") or "").strip() == str(definition_id or "").strip():
			return str(item.get("description") or "").strip()
	return ""


def _definition_business_purpose(definition_id: str) -> str:
	for item in list_business_definition_specs():
		if str(item.get("definition_id") or "").strip() == str(definition_id or "").strip():
			return str(item.get("business_purpose") or "").strip()
	return ""


def _definition_specific_lookup_term(
	definition_id: str,
	*,
	fallback_label: str,
	ambiguous_lookup_value: str = "",
) -> str:
	label_tokens = set(_normalize_phrase(fallback_label).split())
	ambiguous_lookup = _normalize_phrase(ambiguous_lookup_value)
	best_term = ""
	best_score = -1
	best_length = -1
	for item in list_business_definition_specs():
		if str(item.get("definition_id") or "").strip() != str(definition_id or "").strip():
			continue
		lookup_terms = item.get("lookup_terms") if isinstance(item.get("lookup_terms"), list) else []
		for raw_term in lookup_terms:
			clean_term = _clean_subject(raw_term)
			if not clean_term:
				continue
			normalized_term = _normalize_phrase(clean_term)
			if not normalized_term or normalized_term == ambiguous_lookup:
				continue
			term_tokens = set(normalized_term.split())
			score = len(term_tokens & label_tokens)
			if score > best_score or (score == best_score and len(normalized_term) > best_length):
				best_term = clean_term
				best_score = score
				best_length = len(normalized_term)
		break
	return best_term or _clean_subject(fallback_label)


def _source_report_phrase(definition_state: BusinessDefinitionStateContract, formula_state: GovernedFormulaStateContract) -> str:
	source_of_truth = dict(definition_state.source_of_truth or {})
	report_names: List[str] = []
	for key in ("report_name", "report_names"):
		value = source_of_truth.get(key)
		if isinstance(value, list):
			report_names.extend(str(item or "").strip() for item in value if str(item or "").strip())
		elif str(value or "").strip():
			report_names.append(str(value or "").strip())
	if not report_names:
		report_names = [str(value or "").strip() for value in (formula_state.source_reports or []) if str(value or "").strip()]
	return _join_clean(report_names)


def _formula_basis_phrase(definition_state: BusinessDefinitionStateContract, formula_state: GovernedFormulaStateContract) -> str:
	source_of_truth = dict(definition_state.source_of_truth or {})
	numerator = str(source_of_truth.get("numerator_metric") or source_of_truth.get("numerator_basis") or "").strip()
	denominator = str(source_of_truth.get("denominator_metric") or source_of_truth.get("denominator_basis") or "").strip()
	if numerator and denominator:
		return f"{numerator} / {denominator}"
	input_metrics = [str(value or "").strip() for value in (formula_state.input_metrics or []) if str(value or "").strip()]
	if len(input_metrics) == 2 and str(formula_state.formula_type or "").strip() in {"ratio", "sum_divided_by_count"}:
		return f"{_format_title_case_token(input_metrics[0])} / {_format_title_case_token(input_metrics[1])}"
	if len(input_metrics) == 2 and str(formula_state.formula_type or "").strip() == "duration":
		return f"Days between {_format_title_case_token(input_metrics[0])} and {_format_title_case_token(input_metrics[1])}"
	if input_metrics:
		return _join_clean([_format_title_case_token(value) for value in input_metrics])
	return ""


def _definition_rule_notes(definition_id: str, formula_id: str, company_name: str) -> List[str]:
	notes: List[str] = []
	for item in list_business_rule_specs():
		if str(item.get("activation_state") or "").strip() != "active":
			continue
		if not _company_scope_matches(item.get("company_scope"), company_name):
			continue
		scope_type = str(item.get("scope_type") or "").strip()
		scope_reference = str(item.get("scope_reference") or "").strip()
		if scope_type == "definition" and scope_reference == definition_id:
			statement = str(item.get("policy_statement") or "").strip()
			if statement:
				notes.append(statement)
		if scope_type == "formula" and formula_id and scope_reference == formula_id:
			statement = str(item.get("policy_statement") or "").strip()
			if statement:
				notes.append(statement)
	return notes


def _threshold_notes(formula_id: str) -> List[str]:
	notes: List[str] = []
	for item in list_business_threshold_specs_for_formula(formula_id):
		activation_state = str(item.get("activation_state") or "").strip()
		labels = [
			str(band.get("label") or "").strip()
			for band in (item.get("bands") or [])
			if isinstance(band, dict) and str(band.get("label") or "").strip()
		]
		if activation_state == "active":
			if labels:
				notes.append(
					f"Threshold semantics are active with governed bands {', '.join(f'`{label}`' for label in labels)}."
				)
			else:
				notes.append("Threshold semantics are active for this KPI.")
		else:
			blocked_reason = str(item.get("blocked_reason") or "").strip()
			if blocked_reason:
				notes.append(f"Threshold semantics remain blocked for user-facing runtime use: {blocked_reason}")
	return notes


def _build_formula_state_for_display(
	definition_state: BusinessDefinitionStateContract,
	company_name: str,
) -> GovernedFormulaStateContract:
	if not str(definition_state.definition_id or "").strip():
		return build_governed_formula_state_contract(
			requested_definition_id="",
			lookup_value="",
			lookup_mode="definition_id",
			requested_company_name=company_name,
			resolution_state="undefined",
			reason="No definition id was available for governed formula display.",
		)
	return resolve_governed_formula_state(
		definition_state=definition_state,
		company_name=company_name,
	)


def _render_active_answer(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	company_name: str,
	include_business_purpose: bool = False,
) -> str:
	definition_description = _definition_description(definition_state.definition_id)
	if not definition_description:
		definition_description = str(definition_state.reason or "").strip()
	answer_lines = [f"`{definition_state.label}` is defined here as {_lower_first(definition_description)}"]
	business_purpose = _definition_business_purpose(definition_state.definition_id)
	if include_business_purpose and business_purpose:
		answer_lines.append("")
		answer_lines.append(f"It matters because {business_purpose}")
	answer_lines.append("")
	answer_lines.append("Governed Basis")
	answer_lines.append(f"- Definition status: `{definition_state.activation_state or 'active'}`")
	answer_lines.append(f"- Entity grain: {_format_governed_phrase(definition_state.entity_grain)}")
	answer_lines.append(f"- Time basis: {_format_governed_phrase(definition_state.time_basis)}")
	source_report_phrase = _source_report_phrase(definition_state, formula_state)
	if source_report_phrase:
		answer_lines.append(f"- Source reports: {source_report_phrase}")
	formula_basis = _formula_basis_phrase(definition_state, formula_state)
	if formula_basis:
		answer_lines.append(f"- Formula basis: {formula_basis}")
	if str(formula_state.aggregation_rule or "").strip():
		answer_lines.append(f"- Aggregation rule: {_format_governed_phrase(formula_state.aggregation_rule)}")
	policy_notes = _definition_rule_notes(definition_state.definition_id, formula_state.formula_id, company_name)
	threshold_notes = _threshold_notes(formula_state.formula_id)
	if policy_notes or threshold_notes:
		answer_lines.append("")
		answer_lines.append("Policy Notes")
		for item in policy_notes + threshold_notes:
			answer_lines.append(f"- {item}")
	return "\n".join(answer_lines).strip()


def _render_blocked_answer(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	company_name: str,
	include_business_purpose: bool = False,
) -> str:
	definition_description = _definition_description(definition_state.definition_id)
	answer_lines = [
		f"`{definition_state.label}` is defined here, but it is not runtime-active yet.",
		"",
		"Blocked Reason",
		f"- {definition_state.blocked_reason or formula_state.blocked_reason or 'This KPI is not yet approved for runtime use.'}",
	]
	answer_lines.append("")
	answer_lines.append("Intended Governed Basis")
	answer_lines.append(f"- Definition status: `{definition_state.activation_state or 'blocked'}`")
	if definition_description:
		answer_lines.append(f"- Definition: {definition_description}")
	business_purpose = _definition_business_purpose(definition_state.definition_id)
	if include_business_purpose and business_purpose:
		answer_lines.append(f"- Business purpose: {business_purpose}")
	answer_lines.append(f"- Entity grain: {_format_governed_phrase(definition_state.entity_grain)}")
	answer_lines.append(f"- Time basis: {_format_governed_phrase(definition_state.time_basis)}")
	source_report_phrase = _source_report_phrase(definition_state, formula_state)
	if source_report_phrase:
		answer_lines.append(f"- Source reports: {source_report_phrase}")
	formula_basis = _formula_basis_phrase(definition_state, formula_state)
	if formula_basis:
		answer_lines.append(f"- Intended formula basis: {formula_basis}")
	policy_notes = _definition_rule_notes(definition_state.definition_id, formula_state.formula_id, company_name)
	threshold_notes = _threshold_notes(formula_state.formula_id)
	if policy_notes or threshold_notes:
		answer_lines.append("")
		answer_lines.append("Policy Notes")
		for item in policy_notes + threshold_notes:
			answer_lines.append(f"- {item}")
	return "\n".join(answer_lines).strip()


def _render_ambiguous_answer(definition_state: BusinessDefinitionStateContract) -> str:
	answer_lines = [
		f"`{definition_state.lookup_value}` is not a single governed KPI here yet. The approved basis must be clarified first.",
		"",
		"Choose One Governed Definition",
	]
	for item in definition_state.candidate_definitions:
		label = str(item.get("label") or "").strip()
		if label:
			answer_lines.append(f"- {label}")
	return "\n".join(answer_lines).strip()


def _render_undefined_answer(subject: str) -> str:
	answer_lines = [
		f"No governed KPI definition is currently registered for `{subject}`.",
	]
	examples = _generic_kpi_examples()
	if examples:
		answer_lines.append("")
		answer_lines.append("Current Governed KPI Examples")
		for item in examples:
			answer_lines.append(f"- {item}")
	return "\n".join(answer_lines).strip()


def _governed_kpi_continuation_message(
	*,
	label: str,
	query_kind: str,
	include_business_purpose: bool = False,
) -> str:
	clean_label = _clean_subject(label)
	if not clean_label:
		return ""
	if query_kind == "formula":
		return f"what is the formula for {clean_label}"
	if query_kind == "calculation":
		return f"how is {clean_label} calculated"
	if include_business_purpose:
		return f"what is {clean_label} and why does it matter"
	return f"what is {clean_label}"


def _build_ambiguous_clarification_signal(
	*,
	request_id: str,
	definition_state: BusinessDefinitionStateContract,
	answer_text: str,
	query_kind: str,
	include_business_purpose: bool,
) -> Dict[str, Any]:
	options = [
		str(item.get("label") or "").strip()
		for item in (definition_state.candidate_definitions or [])
		if isinstance(item, dict) and str(item.get("label") or "").strip()
	]
	if not options:
		return {}
	resolved_message_by_option = {
		option: _governed_kpi_continuation_message(
			label=_definition_specific_lookup_term(
				str(item.get("definition_id") or "").strip(),
				fallback_label=option,
				ambiguous_lookup_value=str(definition_state.lookup_value or "").strip(),
			),
			query_kind=query_kind,
			include_business_purpose=include_business_purpose,
		)
		for item in (definition_state.candidate_definitions or [])
		if isinstance(item, dict) and str(item.get("label") or "").strip()
		for option in [str(item.get("label") or "").strip()]
	}
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="frontdoor",
		reason_type="governed_kpi_definition_ambiguity",
		user_question=answer_text,
		suggested_options=options,
		internal_reason=(
			"The requested KPI name maps to multiple governed KPI definitions, so the front-door lane "
			"must pause for basis clarification before answering."
		),
		internal_details={
			"continuation_lane": "front_door",
			"continuation_intent_class": "governed_kpi_definition",
			"resolved_message_by_option": resolved_message_by_option,
			"lookup_value": str(definition_state.lookup_value or "").strip(),
			"query_kind": str(query_kind or "").strip(),
			"include_business_purpose": bool(include_business_purpose),
			"candidate_definition_ids": [
				str(item.get("definition_id") or "").strip()
				for item in (definition_state.candidate_definitions or [])
				if isinstance(item, dict) and str(item.get("definition_id") or "").strip()
			],
		},
	).to_payload()


def maybe_build_governed_kpi_frontdoor_response(
	*,
	request_id: str,
	message: str,
	company_name: str = "",
) -> Dict[str, Any]:
	query = _extract_definition_subject(message)
	if not query:
		return {}
	subject = str(query.get("subject") or "").strip()
	query_kind = str(query.get("query_kind") or "").strip()
	include_business_purpose = bool(query.get("include_business_purpose"))
	if _subject_is_dynamic_or_deictic(subject):
		return {}
	resolved_company_name = _current_company_name(company_name)
	definition_state = resolve_business_definition_state(
		subject,
		lookup_mode="lookup_term",
		company_name=resolved_company_name,
	)
	if definition_state.resolution_state == "undefined" and query_kind not in _ALLOWED_UNDEFINED_QUERY_KINDS:
		return {}
	formula_state = build_governed_formula_state_contract(
		requested_definition_id=definition_state.definition_id,
		lookup_value=subject,
		lookup_mode="lookup_term",
		requested_company_name=resolved_company_name,
		resolution_state="undefined",
		reason="No governed formula lookup was attempted.",
	)
	if definition_state.resolution_state in {"active", "blocked"}:
		formula_state = _build_formula_state_for_display(definition_state, resolved_company_name)
	if definition_state.resolution_state == "active":
		answer_text = _render_active_answer(
			definition_state=definition_state,
			formula_state=formula_state,
			company_name=resolved_company_name,
			include_business_purpose=include_business_purpose,
		)
	elif definition_state.resolution_state == "blocked":
		answer_text = _render_blocked_answer(
			definition_state=definition_state,
			formula_state=formula_state,
			company_name=resolved_company_name,
			include_business_purpose=include_business_purpose,
		)
	elif definition_state.resolution_state == "ambiguous":
		answer_text = _render_ambiguous_answer(definition_state)
	else:
		answer_text = _render_undefined_answer(subject)
	clarification_signal_payload: Dict[str, Any] = {}
	if definition_state.resolution_state == "ambiguous":
		clarification_signal_payload = _build_ambiguous_clarification_signal(
			request_id=str(request_id or "").strip(),
			definition_state=definition_state,
			answer_text=answer_text,
			query_kind=query_kind,
			include_business_purpose=include_business_purpose,
		)
	intent_spec = get_frontdoor_intent_spec("governed_kpi_definition")
	if not intent_spec:
		intent_spec = {
			"intent_class_id": "governed_kpi_definition",
			"response_mode": "direct_answer",
			"route_target": "front_door",
			"handle_in_front_door": True,
		}
	reason = (
		f"The turn is a governed KPI definition request for '{subject}', so it should be answered from the approved "
		"business-definition and formula registries."
	)
	semantic_result = SemanticFrontDoorResult(
		status="accepted",
		intent=SemanticFrontDoorIntent(
			intent_class="governed_kpi_definition",
			confidence=1.0,
			reason=reason,
		),
		confidence_threshold=1.0,
	)
	frontdoor_contract = FrontDoorIntentGateContract(
		request_id=str(request_id or "").strip(),
		intent_class="governed_kpi_definition",
		confidence=1.0,
		handle_in_front_door=bool(intent_spec.get("handle_in_front_door", True)),
		response_mode=str(intent_spec.get("response_mode") or "direct_answer").strip() or "direct_answer",
		response_payload={
			"text": answer_text,
			"company_name": resolved_company_name,
			"lookup_value": subject,
			"query_kind": query_kind,
			"include_business_purpose": include_business_purpose,
			"definition_state": definition_state.to_payload(),
			"formula_state": formula_state.to_payload(),
			"clarification_signal_payload": clarification_signal_payload,
		},
		route_target=str(intent_spec.get("route_target") or "front_door").strip() or "front_door",
		reason=reason,
	)
	return {
		"semantic_result": semantic_result,
		"frontdoor_contract": frontdoor_contract,
		"frontdoor_answer": answer_text,
		"definition_state": definition_state.to_payload(),
		"formula_state": formula_state.to_payload(),
		"clarification_signal_payload": clarification_signal_payload,
	}


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


def run_governed_kpi_frontdoor_probe() -> Dict[str, Any]:
	company_name = "Mingalar Mobile Distribution Co., Ltd."
	active = maybe_build_governed_kpi_frontdoor_response(
		request_id="phase2-4-active",
		message="what is credit utilization",
		company_name=company_name,
	)
	active_with_purpose = maybe_build_governed_kpi_frontdoor_response(
		request_id="phase2-4-active-purpose",
		message="what is customer credit utilization and why does it matter",
		company_name=company_name,
	)
	ambiguous = maybe_build_governed_kpi_frontdoor_response(
		request_id="phase2-4-ambiguous",
		message="what is average order value",
		company_name=company_name,
	)
	meaning_with_context = maybe_build_governed_kpi_frontdoor_response(
		request_id="phase2-4-meaning-context",
		message="what does average order value mean in this ERP",
		company_name=company_name,
	)
	blocked = maybe_build_governed_kpi_frontdoor_response(
		request_id="phase2-4-blocked",
		message="what is collection ratio",
		company_name=company_name,
	)
	undefined = maybe_build_governed_kpi_frontdoor_response(
		request_id="phase2-4-undefined",
		message="define gross margin",
		company_name=company_name,
	)
	deictic_passthrough = maybe_build_governed_kpi_frontdoor_response(
		request_id="phase2-4-deictic",
		message="what is this customer's credit limit?",
		company_name=company_name,
	)
	ok = (
		str(((active.get("definition_state") or {}).get("resolution_state") if isinstance(active, dict) else "") or "").strip() == "active"
		and str(((active_with_purpose.get("definition_state") or {}).get("resolution_state") if isinstance(active_with_purpose, dict) else "") or "").strip() == "active"
		and str(((ambiguous.get("definition_state") or {}).get("resolution_state") if isinstance(ambiguous, dict) else "") or "").strip() == "ambiguous"
		and str((((ambiguous.get("clarification_signal_payload") or {}).get("reason_type")) if isinstance(ambiguous, dict) else "") or "").strip() == "governed_kpi_definition_ambiguity"
		and str(((meaning_with_context.get("definition_state") or {}).get("resolution_state") if isinstance(meaning_with_context, dict) else "") or "").strip() == "ambiguous"
		and str(((blocked.get("definition_state") or {}).get("resolution_state") if isinstance(blocked, dict) else "") or "").strip() == "blocked"
		and str(((undefined.get("definition_state") or {}).get("resolution_state") if isinstance(undefined, dict) else "") or "").strip() == "undefined"
		and not deictic_passthrough
	)
	return {
		"ok": ok,
		"active": _probe_safe_response(active),
		"active_with_purpose": _probe_safe_response(active_with_purpose),
		"ambiguous": _probe_safe_response(ambiguous),
		"meaning_with_context": _probe_safe_response(meaning_with_context),
		"blocked": _probe_safe_response(blocked),
		"undefined": _probe_safe_response(undefined),
		"deictic_passthrough": _probe_safe_response(deictic_passthrough),
	}
