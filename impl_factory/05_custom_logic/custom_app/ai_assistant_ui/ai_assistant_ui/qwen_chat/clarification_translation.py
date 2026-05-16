from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	ClarificationReasonContract,
	ClarificationSignalContract,
	build_clarification_reason_contract_from_sources,
	build_clarification_signal_contract,
)
from ai_assistant_ui.qwen_chat.governed_scope_registry import listing_view_display_label
from ai_assistant_ui.qwen_chat.metadata import (
	get_capability_spec,
	entity_grain_display_label,
	financial_statement_display_label,
	financial_statement_report_name,
	get_financial_summary_clarification_spec,
	list_capability_specs,
	list_semantic_resolution_alias_entries,
)
from ai_assistant_ui.qwen_chat.clarification_templates import (
	scope_clarification_question as _scope_clarification_question_helper,
	shared_clarification_question as _shared_clarification_question_helper,
	render_shared_choice_list_clarification as _render_shared_choice_list_clarification_helper,
)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(item or "").strip() for item in values if str(item or "").strip()]


_DEFAULT_TIME_SCOPE_OPTIONS = ["today", "last month", "all time"]


def _capability_business_label(capability_id: str) -> str:
	clean_id = _clean_text(capability_id)
	if not clean_id:
		return ""
	spec = get_capability_spec(clean_id)
	value = _clean_text(spec.get("clarification_business_area_label"))
	if value:
		return value
	for key in ("capability_label", "label", "name"):
		value = _clean_text(spec.get(key))
		if value:
			return value
	return clean_id.replace("_", " ")


def _human_join(values: List[str]) -> str:
	items = [value for value in values if _clean_text(value)]
	if not items:
		return ""
	if len(items) == 1:
		return items[0]
	if len(items) == 2:
		return f"{items[0]} or {items[1]}"
	return f"{', '.join(items[:-1])}, or {items[-1]}"


def _group_business_options(capability_ids: List[str]) -> List[str]:
	capability_set = {_clean_text(value) for value in capability_ids if _clean_text(value)}
	if not capability_set:
		return []
	ranked_labels: List[tuple[int, str]] = []
	for item in list_capability_specs():
		if not isinstance(item, dict):
			continue
		capability_id = _clean_text(item.get("capability_id"))
		if capability_id not in capability_set:
			continue
		label = _clean_text(item.get("clarification_business_area_label")) or _capability_business_label(capability_id)
		if not label:
			continue
		try:
			order = int(item.get("clarification_business_area_order") or 9999)
		except Exception:
			order = 9999
		ranked_labels.append((order, label))
	ranked_labels.sort(key=lambda item: (item[0], item[1].lower()))
	options: List[str] = []
	for _, label in ranked_labels:
		if label not in options:
			options.append(label)
	return options[:5]


def _default_capability_missing_options() -> List[str]:
	ranked_labels: List[tuple[int, str]] = []
	for item in list_capability_specs():
		if not isinstance(item, dict):
			continue
		label = _clean_text(item.get("clarification_business_area_label"))
		if not label:
			continue
		try:
			order = int(item.get("clarification_business_area_order") or 9999)
		except Exception:
			order = 9999
		ranked_labels.append((order, label))
	ranked_labels.sort(key=lambda item: (item[0], item[1].lower()))
	options: List[str] = []
	for _, label in ranked_labels:
		if label not in options:
			options.append(label)
	return options[:5]


def _time_scope_options(details: Dict[str, Any]) -> List[str]:
	options = _clean_list(details.get("suggested_time_scope_options"))
	return options or list(_DEFAULT_TIME_SCOPE_OPTIONS)


def _report_option_bindings_by_option(options: List[str]) -> Dict[str, Dict[str, Any]]:
	statement_alias_entries = list_semantic_resolution_alias_entries("statement_variant")
	statement_aliases_by_canonical = {
		_clean_text(item.get("canonical_value")): _clean_list(item.get("aliases"))
		for item in statement_alias_entries
		if _clean_text(item.get("canonical_value"))
	}
	financial_statement_spec = get_capability_spec("financial_statement_read")
	fresh_query_defaults = (
		financial_statement_spec.get("fresh_query_defaults")
		if isinstance(financial_statement_spec.get("fresh_query_defaults"), dict)
		else {}
	)
	report_name_by_canonical: Dict[str, str] = {}
	canonical_values_by_report: Dict[str, set[str]] = {}
	for defaults_key in ("financial_statement", "financial_summary"):
		defaults = fresh_query_defaults.get(defaults_key) if isinstance(fresh_query_defaults.get(defaults_key), dict) else {}
		mapping = defaults.get("report_overrides_by_concept") if isinstance(defaults.get("report_overrides_by_concept"), dict) else {}
		for canonical_value, report_name in mapping.items():
			clean_report_name = _clean_text(report_name)
			clean_canonical_value = _clean_text(canonical_value)
			if clean_report_name and clean_canonical_value:
				report_name_by_canonical.setdefault(clean_canonical_value, clean_report_name)
				canonical_values_by_report.setdefault(clean_report_name, set()).add(clean_canonical_value)

	def _matches_phrase(option_text: str, candidate_text: str) -> bool:
		return _clean_text(option_text).lower() == _clean_text(candidate_text).lower()

	out: Dict[str, Dict[str, Any]] = {}
	for option in options:
		clean_option = _clean_text(option)
		if not clean_option:
			continue
		canonical_value = ""
		for candidate in sorted(canonical_values_by_report.get(clean_option, set())):
			canonical_value = candidate
			break
		if not canonical_value:
			for candidate_canonical, aliases in statement_aliases_by_canonical.items():
				match_phrases = [candidate_canonical.replace("_", " ")] + list(aliases)
				if any(_matches_phrase(clean_option, phrase) for phrase in match_phrases):
					canonical_value = candidate_canonical
					break
		if not canonical_value:
			continue
		report_name = (
			financial_statement_report_name(canonical_value)
			or report_name_by_canonical.get(canonical_value, clean_option)
		)
		aliases = list(statement_aliases_by_canonical.get(canonical_value, []))
		if report_name:
			aliases.append(report_name)
		out[clean_option] = {
			"statement_variant": canonical_value,
			"report_name": report_name,
			"display_label": financial_statement_display_label(canonical_value) or report_name,
			"aliases": list(dict.fromkeys([alias for alias in aliases if _clean_text(alias) and _clean_text(alias) != clean_option])),
		}
	return out


def _report_option_aliases_by_option(options: List[str]) -> Dict[str, List[str]]:
	bindings = _report_option_bindings_by_option(options)
	return {
		option: _clean_list(binding.get("aliases"))
		for option, binding in bindings.items()
		if _clean_list(binding.get("aliases"))
	}


def _report_option_slot_values_by_option(options: List[str]) -> Dict[str, str]:
	bindings = _report_option_bindings_by_option(options)
	return {
		option: _clean_text(binding.get("statement_variant"))
		for option, binding in bindings.items()
		if _clean_text(binding.get("statement_variant"))
	}


def _report_option_report_names_by_option(options: List[str]) -> Dict[str, str]:
	bindings = _report_option_bindings_by_option(options)
	return {
		option: _clean_text(binding.get("report_name"))
		for option, binding in bindings.items()
		if _clean_text(binding.get("report_name"))
	}


def _report_option_display_labels_by_option(options: List[str]) -> Dict[str, str]:
	bindings = _report_option_bindings_by_option(options)
	return {
		option: _clean_text(binding.get("display_label"))
		for option, binding in bindings.items()
		if _clean_text(binding.get("display_label"))
	}


def _report_option_resolved_message_by_option(options: List[str]) -> Dict[str, str]:
	report_names = _report_option_report_names_by_option(options)
	return {
		option: f"show me {report_name}"
		for option, report_name in report_names.items()
		if _clean_text(option) and _clean_text(report_name)
	}


def _scope_clarification_question(
	*,
	reason_type: str,
	template_group: str,
	variant: str,
	default_question: str = "",
	template_values: Dict[str, str],
) -> str:
	return _scope_clarification_question_helper(
		reason_type=reason_type,
		template_group=template_group,
		variant=variant,
		default_question=default_question,
		template_values=template_values,
	)


def _shared_clarification_question(
	*,
	reason_type: str,
	variant: str,
	default_question: str = "",
	template_values: Dict[str, str],
) -> str:
	return _shared_clarification_question_helper(
		reason_type=reason_type,
		variant=variant,
		default_question=default_question,
		template_values=template_values,
	)


def render_shared_choice_list_clarification(
	*,
	reason_type: str,
	variant: str,
	template_values: Dict[str, str],
	options: List[str],
	default_question: str = "",
	default_heading: str = "Choose one:",
) -> str:
	return _render_shared_choice_list_clarification_helper(
		reason_type=reason_type,
		variant=variant,
		template_values=template_values,
		options=options,
		default_question=default_question,
		default_heading=default_heading,
	)


def render_clarification_signal_user_text(
	signal_payload: Dict[str, Any],
	*,
	max_inline_options: int = 5,
) -> str:
	if not isinstance(signal_payload, dict):
		return ""
	question = _clean_text(signal_payload.get("user_question"))
	options = _clean_list(signal_payload.get("suggested_options"))
	internal_details = (
		signal_payload.get("internal_details")
		if isinstance(signal_payload.get("internal_details"), dict)
		else {}
	)
	if not question:
		return ""
	if not bool(internal_details.get("inline_options_on_first_turn")):
		return question
	if not options or len(options) > int(max(1, max_inline_options)):
		return question
	normalized_question = question.lower()
	if len([option for option in options if _clean_text(option).lower() in normalized_question]) >= len(options):
		return question
	list_heading = _clean_text(internal_details.get("inline_option_heading")) or "Here are the options I found:"
	lines = [question, ""]
	if list_heading:
		lines.append(list_heading)
	for option in options:
		lines.append(f"- {option}")
	return "\n".join(lines).strip()


def _with_clarification_template_group(
	details: Dict[str, Any],
	*,
	template_group: str,
	**extra_fields: Any,
) -> Dict[str, Any]:
	out = dict(details or {})
	clean_group = _clean_text(template_group)
	if clean_group:
		out["clarification_template_group"] = clean_group
	for key, value in extra_fields.items():
		if value not in (None, ""):
			out[str(key or "").strip()] = value
	return out


def _unsupported_scope_variant(
	*,
	requested_label: str,
	supported_options: List[str],
) -> str:
	if requested_label and supported_options:
		return "requested_and_supported"
	if requested_label:
		return "requested_only"
	if supported_options:
		return "supported_only"
	return "default"


def _build_unsupported_scope_clarification_signal(
	*,
	request_id: str,
	reason_type: str,
	internal_reason: str,
	details: Dict[str, Any],
	requested_label: str,
	supported_options: List[str],
) -> ClarificationSignalContract:
	clean_requested_label = _clean_text(requested_label)
	clean_supported_options = list(dict.fromkeys([value for value in supported_options if _clean_text(value)]))
	variant = _unsupported_scope_variant(
		requested_label=clean_requested_label,
		supported_options=clean_supported_options,
	)
	question = _scope_clarification_question(
		reason_type=reason_type,
		template_group="unsupported_scope_clarification",
		variant=variant,
		template_values={
			"requested_label": clean_requested_label,
			"supported_options": _human_join(clean_supported_options),
		},
	)
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="compiler",
		reason_type=reason_type,
		user_question=question,
		suggested_options=clean_supported_options[:5],
		internal_reason=_clean_text(internal_reason),
		internal_details=_with_clarification_template_group(
			details,
			template_group="unsupported_scope_clarification",
			requested_label=clean_requested_label,
		),
	)


def _build_shared_clarification_signal(
	*,
	request_id: str,
	reason_type: str,
	internal_reason: str,
	details: Dict[str, Any],
	suggested_options: List[str] | None = None,
	variant: str = "default",
	template_values: Dict[str, str] | None = None,
	extra_internal_details: Dict[str, Any] | None = None,
	stage: str = "compiler",
) -> ClarificationSignalContract:
	clean_options = list(dict.fromkeys([value for value in (suggested_options or []) if _clean_text(value)]))
	merged_details = {
		**dict(details or {}),
		**(dict(extra_internal_details or {}) if isinstance(extra_internal_details, dict) else {}),
	}
	return build_clarification_signal_contract(
		request_id=request_id,
		stage=stage,
		reason_type=reason_type,
		user_question=_shared_clarification_question(
			reason_type=reason_type,
			variant=variant,
			template_values=dict(template_values or {}),
		),
		suggested_options=clean_options,
		internal_reason=_clean_text(internal_reason),
		internal_details=_with_clarification_template_group(
			merged_details,
			template_group="shared_clarification",
		),
	)


def _translate_financial_summary_signal(
	*,
	request_id: str,
	reason_type: str,
	compiler_reason: str,
	compiler_details: Dict[str, Any],
) -> ClarificationSignalContract | None:
	spec = get_financial_summary_clarification_spec(reason_type)
	if not spec:
		return None
	details = dict(compiler_details or {})
	for key in (
		"option_aliases_by_option",
		"resolved_message_by_option",
		"resolved_message_template",
		"resolved_message_placeholder",
		"semantic_slot_name",
		"semantic_slot_value_by_option",
		"resolved_slot_payload_by_option",
		"selected_report_by_option",
		"carryover_slot_values",
		"continuation_lane",
	):
		if key not in details and key in spec:
			details[key] = spec.get(key)
	question = _clean_text(details.get("user_question")) or _clean_text(spec.get("user_question"))
	options = _clean_list(details.get("suggested_options")) or _clean_list(spec.get("suggested_options"))
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="compiler",
		reason_type=reason_type,
		user_question=question,
		suggested_options=options,
		internal_reason=_clean_text(compiler_reason),
		internal_details=_with_clarification_template_group(
			details,
			template_group="shared_clarification",
		),
	)


def _translate_compiler_signal(
	*,
	request_id: str,
	compiler_reason: str,
	compiler_reason_type: str,
	compiler_details: Dict[str, Any],
) -> ClarificationSignalContract:
	reason_type = _clean_text(compiler_reason_type)
	details = dict(compiler_details or {})
	if reason_type == "capability_ambiguity":
		options = _group_business_options(_clean_list(details.get("capability_candidates")))
		return _build_shared_clarification_signal(
			request_id=request_id,
			reason_type=reason_type,
			internal_reason=compiler_reason,
			details=details,
			suggested_options=options,
			variant="with_options" if options else "default",
			template_values={"supported_options": _human_join(options)},
		)
	if reason_type == "report_ambiguity":
		options = _clean_list(details.get("report_candidates"))
		option_aliases_by_option = _report_option_aliases_by_option(options)
		option_slot_values_by_option = _report_option_slot_values_by_option(options)
		option_report_names_by_option = _report_option_report_names_by_option(options)
		option_display_labels_by_option = _report_option_display_labels_by_option(options)
		resolved_message_by_option = _report_option_resolved_message_by_option(options)
		variant = "default"
		supported_options = _human_join(list(dict.fromkeys(options))[:3])
		financial_view_values = {
			value
			for value in option_slot_values_by_option.values()
			if value in {"profit_and_loss", "balance_sheet", "cash_flow"}
		}
		if financial_view_values:
			variant = "financial_views"
			financial_labels = [
				option_display_labels_by_option.get(option) or option
				for option in options
				if _clean_text(option_display_labels_by_option.get(option) or option)
			]
			supported_options = _human_join(list(dict.fromkeys(financial_labels))[:3])
		elif options:
			variant = "with_options"
		return _build_shared_clarification_signal(
			request_id=request_id,
			reason_type=reason_type,
			internal_reason=compiler_reason,
			details=details,
			suggested_options=list(dict.fromkeys(options))[:5],
			variant=variant,
			template_values={"supported_options": supported_options},
			extra_internal_details={
				"option_aliases_by_option": option_aliases_by_option,
				"semantic_slot_name": "statement_variant" if option_slot_values_by_option else "",
				"semantic_slot_value_by_option": option_slot_values_by_option,
				"selected_report_by_option": option_report_names_by_option,
				"resolved_message_by_option": resolved_message_by_option,
				"continuation_lane": "front_door",
			},
		)
	if reason_type == "time_scope_missing":
		return _build_shared_clarification_signal(
			request_id=request_id,
			reason_type=reason_type,
			internal_reason=compiler_reason,
			details=details,
			suggested_options=_time_scope_options(details),
		)
	if reason_type == "filter_missing":
		return _build_shared_clarification_signal(
			request_id=request_id,
			reason_type=reason_type,
			internal_reason=compiler_reason,
			details=details,
		)
	if reason_type == "capability_missing":
		suggested_options = _default_capability_missing_options()
		return _build_shared_clarification_signal(
			request_id=request_id,
			reason_type=reason_type,
			internal_reason=compiler_reason,
			details=details,
			suggested_options=suggested_options,
			template_values={"supported_options": _human_join(suggested_options)},
		)
	if reason_type == "request_underspecified":
		return _build_shared_clarification_signal(
			request_id=request_id,
			reason_type=reason_type,
			internal_reason=compiler_reason,
			details=details,
		)
	if reason_type == "transaction_listing_surface_unsupported":
		requested_view = _clean_text(details.get("requested_listing_view"))
		requested_label = listing_view_display_label(requested_view, plural=True, lowercase=True)
		supported_views = [
			listing_view_display_label(value, plural=True, lowercase=True)
			for value in _clean_list(details.get("supported_listing_views"))
			if _clean_text(value)
		]
		return _build_unsupported_scope_clarification_signal(
			request_id=request_id,
			reason_type=reason_type,
			internal_reason=compiler_reason,
			details=details,
			requested_label=requested_label,
			supported_options=supported_views,
		)
	if reason_type == "master_data_scope_unsupported":
		requested_grain = _clean_text(details.get("requested_entity_grain"))
		requested_label = entity_grain_display_label(requested_grain, plural=True)
		supported_grains = [
			entity_grain_display_label(value, plural=True)
			for value in _clean_list(details.get("supported_entity_grains"))
			if _clean_text(value)
		]
		return _build_unsupported_scope_clarification_signal(
			request_id=request_id,
			reason_type=reason_type,
			internal_reason=compiler_reason,
			details=details,
			requested_label=requested_label,
			supported_options=supported_grains,
		)
	financial_summary_signal = _translate_financial_summary_signal(
		request_id=request_id,
		reason_type=reason_type,
		compiler_reason=compiler_reason,
		compiler_details=details,
	)
	if financial_summary_signal is not None:
		return financial_summary_signal
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="compiler",
		reason_type=reason_type or "generic_clarification",
		user_question=_shared_clarification_question(
			reason_type="generic_clarification",
			variant="default",
			template_values={},
		),
		suggested_options=[],
		internal_reason=_clean_text(compiler_reason),
		internal_details=_with_clarification_template_group(
			details,
			template_group="shared_clarification",
		),
	)


def _translate_validation_signal(
	*,
	request_id: str,
	stage: str,
	validation_payload: Dict[str, Any],
) -> ClarificationSignalContract:
	payload = dict(validation_payload or {})
	reason_type = "validation_clarification"
	user_question = "I need one more detail before I can answer this confidently."
	suggested_options: List[str] = []
	if payload.get("time_scope_match") is False:
		reason_type = "time_scope_clarification"
		suggested_options = list(_DEFAULT_TIME_SCOPE_OPTIONS)
	return _build_shared_clarification_signal(
		request_id=request_id,
		reason_type=reason_type,
		internal_reason=_clean_text(payload.get("decision")),
		details=payload,
		suggested_options=suggested_options,
		stage=stage,
	)


def translate_clarification_reason_contract(
	*,
	reason_contract: ClarificationReasonContract,
) -> ClarificationSignalContract:
	stage = _clean_text(reason_contract.stage)
	reason_type = _clean_text(reason_contract.reason_type)
	details = dict(reason_contract.internal_details or {})
	internal_reason = _clean_text(reason_contract.internal_reason)
	if stage == "compiler" or reason_type in {"report_ambiguity", "capability_ambiguity", "time_scope_missing", "filter_missing", "capability_missing", "request_underspecified"}:
		return _translate_compiler_signal(
			request_id=reason_contract.request_id,
			compiler_reason=internal_reason,
			compiler_reason_type=reason_type,
			compiler_details=details,
		)
	return _translate_validation_signal(
		request_id=reason_contract.request_id,
		stage=stage or "validation",
		validation_payload=details,
	)


def translate_clarification_signal(
	*,
	request_id: str,
	raw_message: str = "",
	compiler_reason: str = "",
	compiler_reason_type: str = "",
	compiler_details: Dict[str, Any] | None = None,
	family_validation: Dict[str, Any] | None = None,
	semantic_validation: Dict[str, Any] | None = None,
) -> ClarificationSignalContract:
	_ = _clean_text(raw_message)
	reason_contract = build_clarification_reason_contract_from_sources(
		request_id=request_id,
		compiler_reason=compiler_reason,
		compiler_reason_type=compiler_reason_type,
		compiler_details=dict(compiler_details or {}),
		family_validation=dict(family_validation or {}) if isinstance(family_validation, dict) else None,
		semantic_validation=dict(semantic_validation or {}) if isinstance(semantic_validation, dict) else None,
	)
	if reason_contract is not None:
		return translate_clarification_reason_contract(reason_contract=reason_contract)
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="unknown",
		reason_type="generic_clarification",
		user_question=_shared_clarification_question(
			reason_type="generic_clarification",
			variant="default",
			template_values={},
		),
		suggested_options=[],
		internal_reason="",
		internal_details={"clarification_template_group": "shared_clarification"},
	)
