from __future__ import annotations

import difflib
import json
import re
from typing import Any, Dict, List, Tuple

from ai_assistant_ui.qwen_chat.compiler import compile_fresh_query
from ai_assistant_ui.qwen_chat.clarification_state import (
	build_pending_clarification_state,
	ClarificationState,
	get_clarification_state,
	store_clarification_state,
)
from ai_assistant_ui.qwen_chat.contracts import (
	_message_looks_like_self_contained_governed_business_query,
	build_clarification_resolution_contract,
)
from ai_assistant_ui.qwen_chat.entity_reference_resolution import (
	normalize_master_data_lookup_slots,
	resolve_entity_reference_from_message,
)
from ai_assistant_ui.qwen_chat.conversation_control_language import (
	classify_conversation_control_evidence as _classify_conversation_control_evidence,
	looks_like_option_list_request as _shared_looks_like_option_list_request,
)
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import interpret_fresh_query_semantically
from ai_assistant_ui.qwen_chat.governed_composite_runtime_execution import (
	maybe_build_governed_composite_frontdoor_response,
)
from ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution import (
	maybe_build_governed_kpi_value_frontdoor_response,
)
from ai_assistant_ui.qwen_chat.governed_kpi_support import maybe_build_governed_kpi_frontdoor_response
from ai_assistant_ui.qwen_chat.master_data_frontdoor_support import (
	assess_master_data_frontdoor_request,
)
from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import interpret_front_door_semantically
from ai_assistant_ui.qwen_chat.metadata import (
	entity_grain_display_label,
	financial_statement_report_name,
	get_capability_spec,
	get_scope_clarification_template_spec,
	list_semantic_resolution_alias_entries,
	ontology_detect_concepts,
)
from ai_assistant_ui.qwen_chat.semantic_resolution_registry import semantic_slot_alias_matches


def _normalize_text(value: Any) -> str:
	return " ".join(str(value or "").strip().lower().split())


def _message_contains_phrase(value: str, phrase: str) -> bool:
	text = _normalize_text(value)
	target = _normalize_text(phrase)
	if not text or not target:
		return False
	pattern = r"(^|[^a-z0-9])" + re.escape(target) + r"([^a-z0-9]|$)"
	return bool(re.search(pattern, text))


def _semantic_slot_alias_matches(slot_name: str, message: str) -> List[str]:
	return semantic_slot_alias_matches(slot_name, message)


def _financial_statement_family_aliases() -> List[str]:
	spec = get_capability_spec("financial_statement_read")
	if not spec:
		return []
	aliases = set()
	for raw_value in [
		spec.get("label"),
		spec.get("clarification_business_area_label"),
		*(spec.get("intent_classes") or []),
	]:
		normalized_value = _normalize_text(raw_value)
		if not normalized_value:
			continue
		aliases.add(normalized_value)
		if normalized_value.endswith(" read"):
			aliases.add(normalized_value[: -len(" read")].strip())
		aliases.add(normalized_value.replace("_", " "))
	return [alias for alias in aliases if alias]


def _visible_message_text(role: str, content: str) -> str:
	text = str(content or "").strip()
	if not text:
		return ""
	if str(role or "").strip().lower() != "assistant":
		return text
	try:
		payload = json.loads(text)
	except Exception:
		return text
	if isinstance(payload, dict):
		payload_type = str(payload.get("type") or "").strip().lower()
		payload_text = str(payload.get("text") or "").strip()
		if payload_type in {"text", "error"} and payload_text:
			return payload_text
	return text


def _parse_payload(content: str) -> Dict[str, Any]:
	try:
		obj = json.loads(str(content or ""))
	except Exception:
		return {}
	return obj if isinstance(obj, dict) else {}


def latest_pending_clarification_signal_from_messages(session_doc) -> Dict[str, Any]:
	messages = list(session_doc.get("messages") or [])
	latest_assistant_index = -1
	latest_assistant_text = ""
	for idx in range(len(messages) - 1, -1, -1):
		row = messages[idx]
		if str(row.role or "").strip().lower() != "assistant":
			continue
		latest_assistant_index = idx
		latest_assistant_text = _visible_message_text("assistant", str(row.content or "")).strip()
		break
	if latest_assistant_index < 0 or not latest_assistant_text:
		return {}

	signal_payload: Dict[str, Any] = {}
	signal_index = -1
	for offset, row in enumerate(messages[latest_assistant_index + 1 :], start=latest_assistant_index + 1):
		if str(row.role or "").strip().lower() != "tool":
			continue
		payload = _parse_payload(str(row.content or ""))
		if str(payload.get("type") or "").strip() == "qwen_clarification_signal_contract":
			signal_payload = payload
			signal_index = offset
	if not signal_payload:
		return {}
	if str(signal_payload.get("user_question") or "").strip() != latest_assistant_text:
		return {}
	for row in messages[signal_index + 1 :]:
		role = str(row.role or "").strip().lower()
		if role in {"user", "assistant"} and _visible_message_text(role, str(row.content or "")).strip():
			return {}
	return signal_payload


def latest_pending_clarification_signal(session_doc) -> Dict[str, Any]:
	stored_state = get_clarification_state(session_doc)
	if stored_state.has_pending:
		return dict(stored_state.pending_signal)
	return latest_pending_clarification_signal_from_messages(session_doc)


def latest_assistant_turn_was_clarification_fallback_stop(session_doc) -> bool:
	messages = list(session_doc.get("messages") or [])
	latest_assistant_index = -1
	for idx in range(len(messages) - 1, -1, -1):
		row = messages[idx]
		if str(row.role or "").strip().lower() != "assistant":
			continue
		if not _visible_message_text("assistant", str(row.content or "")).strip():
			continue
		latest_assistant_index = idx
		break
	if latest_assistant_index < 0:
		return False
	for idx in range(latest_assistant_index - 1, -1, -1):
		row = messages[idx]
		role = str(row.role or "").strip().lower()
		if role in {"user", "assistant"}:
			break
		if role != "tool":
			continue
		payload = _parse_payload(str(row.content or ""))
		if str(payload.get("type") or "").strip() != "qwen_phase55_observability_event":
			continue
		if str(payload.get("event_family") or "").strip() != "clarification":
			continue
		return str(payload.get("event_name") or "").strip() == "fallback_stop"
	return False


def store_pending_clarification_signal(
	session_doc,
	signal_payload: Dict[str, Any],
	*,
	attempt_count: int = 0,
	max_attempts: int = 3,
) -> None:
	state = build_pending_clarification_state(
		signal_payload,
		attempt_count=attempt_count,
		max_attempts=max_attempts,
	)
	store_clarification_state(session_doc, state)


def clear_pending_clarification_signal(session_doc) -> None:
	store_clarification_state(session_doc, build_pending_clarification_state({}))


def _human_join(values: List[str]) -> str:
	items = [str(value or "").strip() for value in (values or []) if str(value or "").strip()]
	if not items:
		return ""
	if len(items) == 1:
		return items[0]
	if len(items) == 2:
		return f"{items[0]} or {items[1]}"
	return f"{', '.join(items[:-1])}, or {items[-1]}"


def _message_template_placeholders(template: str) -> List[str]:
	return list(
		dict.fromkeys(
			[
				str(value or "").strip()
				for value in re.findall(r"\{([A-Za-z0-9_]+)\}", str(template or ""))
				if str(value or "").strip()
			]
		)
	)


def _render_shared_clarification_response(
	*,
	reason_type: str,
	response_kind: str,
	options: List[str],
	default_message: str,
) -> str:
	spec = get_scope_clarification_template_spec(
		reason_type,
		template_group="shared_clarification",
	)
	response_templates = spec.get("response_templates") if isinstance(spec.get("response_templates"), dict) else {}
	variant = "with_options" if options else "default"
	template = str(
		response_templates.get(f"{response_kind}_{variant}")
		or response_templates.get(f"{response_kind}_default")
		or ""
	).strip()
	if not template:
		return default_message
	try:
		return template.format(supported_options=_human_join(options))
	except KeyError:
		return default_message


def _default_template_group_for_reason(reason_type: str) -> str:
	clean_reason = str(reason_type or "").strip()
	if clean_reason in {
		"capability_ambiguity",
		"report_ambiguity",
		"time_scope_missing",
		"time_scope_clarification",
		"filter_missing",
		"capability_missing",
		"request_underspecified",
		"validation_clarification",
		"generic_clarification",
		"governed_kpi_definition_ambiguity",
		"composite_family_variation",
	}:
		return "shared_clarification"
	if clean_reason in {"master_data_scope_unsupported", "transaction_listing_surface_unsupported"}:
		return "unsupported_scope_clarification"
	return ""


def _clarification_template_group(signal_payload: Dict[str, Any]) -> str:
	internal_details = signal_payload.get("internal_details")
	if isinstance(internal_details, dict):
		explicit_group = str(internal_details.get("clarification_template_group") or "").strip()
		if explicit_group:
			return explicit_group
	return _default_template_group_for_reason(str(signal_payload.get("reason_type") or "").strip())


def _clarification_requested_label(signal_payload: Dict[str, Any]) -> str:
	internal_details = signal_payload.get("internal_details")
	if not isinstance(internal_details, dict):
		return ""
	return str(internal_details.get("requested_label") or "").strip()


def _render_declared_clarification_response(
	*,
	signal_payload: Dict[str, Any],
	response_kind: str,
	default_message: str,
) -> str:
	reason_type = str(signal_payload.get("reason_type") or "").strip()
	template_group = _clarification_template_group(signal_payload)
	if not reason_type or not template_group:
		return default_message
	spec = get_scope_clarification_template_spec(reason_type, template_group=template_group)
	response_templates = spec.get("response_templates") if isinstance(spec.get("response_templates"), dict) else {}
	if not response_templates:
		return default_message
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	requested_label = _clarification_requested_label(signal_payload)
	candidate_keys: List[str] = []
	if requested_label and options:
		candidate_keys.append(f"{response_kind}_requested_and_supported")
	if requested_label:
		candidate_keys.append(f"{response_kind}_requested_only")
	if options:
		candidate_keys.extend([f"{response_kind}_supported_only", f"{response_kind}_with_options"])
	candidate_keys.append(f"{response_kind}_default")
	template = ""
	for key in candidate_keys:
		template = str(response_templates.get(key) or "").strip()
		if template:
			break
	if not template:
		return default_message
	try:
		return template.format(
			supported_options=_human_join(options),
			requested_label=requested_label,
		)
	except KeyError:
		return default_message


def _word_tokens(value: str) -> List[str]:
	return re.findall(r"[A-Za-z0-9]+", str(value or "").lower())


def _token_key(value: str) -> str:
	return " ".join(_word_tokens(value))


_GENERIC_CLARIFICATION_ABBREVIATION_STOP_WORDS = {"and", "or", "the", "a", "an", "of", "to", "for", "by", "statement", "report", "view"}
_GENERIC_CLARIFICATION_DESCRIPTOR_TOKENS = {"statement", "report", "view"}


def _token_variants(value: str) -> List[str]:
	tokens = _word_tokens(value)
	if not tokens:
		return []
	variants: List[str] = []
	joined = " ".join(tokens)
	if joined:
		variants.append(joined)
	if len(tokens) >= 2 and all(len(token) == 1 for token in tokens):
		variants.append("".join(tokens))
	return list(dict.fromkeys([variant for variant in variants if variant]))


def _candidate_phrase_variants(value: str) -> List[str]:
	clean_value = str(value or "").strip()
	if not clean_value:
		return []
	tokens = _word_tokens(clean_value)
	variants: List[str] = []
	joined_tokens = " ".join(tokens)
	if joined_tokens:
		variants.append(joined_tokens)
	significant_tokens = [token for token in tokens if token not in _GENERIC_CLARIFICATION_ABBREVIATION_STOP_WORDS]
	if len(significant_tokens) >= 2:
		acronym = "".join(token[0] for token in significant_tokens)
		if len(acronym) >= 2:
			variants.append(acronym)
			descriptor_tokens = [token for token in tokens if token in _GENERIC_CLARIFICATION_DESCRIPTOR_TOKENS]
			if descriptor_tokens:
				variants.append(f"{acronym} {descriptor_tokens[-1]}")
	return list(dict.fromkeys([variant for variant in variants if variant]))


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _report_option_bindings_by_option(options: List[str]) -> Dict[str, Dict[str, Any]]:
	statement_alias_entries = list_semantic_resolution_alias_entries("statement_variant")
	statement_aliases_by_canonical = {
		str(item.get("canonical_value") or "").strip(): _clean_list(item.get("aliases"))
		for item in statement_alias_entries
		if str(item.get("canonical_value") or "").strip()
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
			clean_report_name = str(report_name or "").strip()
			clean_canonical_value = str(canonical_value or "").strip()
			if clean_report_name and clean_canonical_value:
				report_name_by_canonical.setdefault(clean_canonical_value, clean_report_name)
				canonical_values_by_report.setdefault(clean_report_name, set()).add(clean_canonical_value)

	def _matches_phrase(option_text: str, candidate_text: str) -> bool:
		return _normalize_text(option_text) == _normalize_text(candidate_text)

	out: Dict[str, Dict[str, Any]] = {}
	for option in options:
		clean_option = str(option or "").strip()
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
			"aliases": list(dict.fromkeys([alias for alias in aliases if str(alias or "").strip() and str(alias or "").strip() != clean_option])),
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
		option: str(binding.get("statement_variant") or "").strip()
		for option, binding in bindings.items()
		if str(binding.get("statement_variant") or "").strip()
	}


def _report_option_report_names_by_option(options: List[str]) -> Dict[str, str]:
	bindings = _report_option_bindings_by_option(options)
	return {
		option: str(binding.get("report_name") or "").strip()
		for option, binding in bindings.items()
		if str(binding.get("report_name") or "").strip()
	}


def _looks_like_meta_question(message: str) -> bool:
	text = str(message or "").strip()
	if not text:
		return False
	return "?" in text


def _looks_like_option_list_request(message: str) -> bool:
	return _shared_looks_like_option_list_request(message)


def _control_evidence_payload(message: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
	if isinstance(payload, dict) and payload:
		return dict(payload)
	return dict(_classify_conversation_control_evidence(message) or {})


def _looks_like_empty_ack(message: str) -> bool:
	text = str(message or "").strip()
	if not text:
		return False
	if "?" in text:
		return False
	return len(_word_tokens(text)) <= 2


def looks_like_short_acknowledgement(message: str) -> bool:
	return _looks_like_empty_ack(message)


def _match_pending_clarification_option(
	message: str,
	options: List[str],
	option_aliases_by_option: Dict[str, List[str]] | None = None,
) -> Tuple[str, str, float]:
	normalized_message = _normalize_text(message)
	if not normalized_message:
		return "", "", 0.0
	message_token_keys = set(_token_variants(message))
	unique_options = [str(option or "").strip() for option in (options or []) if str(option or "").strip()]
	if not unique_options:
		return "", "", 0.0
	normalized_options = {_normalize_text(option): option for option in unique_options}
	if normalized_message in normalized_options:
		return normalized_options[normalized_message], "exact", 1.0
	option_aliases_by_option = dict(option_aliases_by_option or {})
	for idx, option in enumerate(unique_options, start=1):
		ordinal_aliases = [
			f"option {idx}",
			f"number {idx}",
			f"no {idx}",
			f"#{idx}",
			f"the number {idx}",
		]
		if idx == 1:
			ordinal_aliases.extend(["first", "1st", "the first", "the first one"])
		elif idx == 2:
			ordinal_aliases.extend(["second", "2nd", "the second", "the second one"])
		elif idx == 3:
			ordinal_aliases.extend(["third", "3rd", "the third", "the third one"])
		elif idx == 4:
			ordinal_aliases.extend(["fourth", "4th", "the fourth", "the fourth one"])
		elif idx == 5:
			ordinal_aliases.extend(["fifth", "5th", "the fifth", "the fifth one"])
		elif idx == len(unique_options):
			ordinal_aliases.extend(["last", "the last", "the last one"])
		existing_aliases = list(option_aliases_by_option.get(option) or [])
		option_aliases_by_option[option] = list(
			dict.fromkeys([alias for alias in existing_aliases + ordinal_aliases if _normalize_text(alias)])
		)
	if message_token_keys:
		message_tokens = set(normalized_message.split())
		for option in unique_options:
			for variant in _candidate_phrase_variants(option):
				if variant in message_token_keys:
					return option, "exact_token", 0.99
			option_tokens = set(_normalize_text(option).split())
			if len(option_tokens) >= 2 and option_tokens.issubset(message_tokens):
				return option, "exact_token", 0.98
			for alias in (option_aliases_by_option.get(option) or []):
				if normalized_message == _normalize_text(alias):
					return option, "exact_alias", 0.97
				for variant in _candidate_phrase_variants(alias):
					if variant in message_token_keys:
						return option, "exact_token_alias", 0.97
				alias_tokens = set(_normalize_text(alias).split())
				if len(alias_tokens) >= 2 and alias_tokens.issubset(message_tokens):
					return option, "exact_token_alias", 0.96
	else:
		for option in unique_options:
			for alias in (option_aliases_by_option.get(option) or []):
				if normalized_message == _normalize_text(alias):
					return option, "exact_alias", 0.97
	best_fuzzy_option = ""
	best_fuzzy_score = 0.0
	second_fuzzy_score = 0.0
	best_fuzzy_mode = ""
	for option in unique_options:
		candidate_phrases = [str(option or "").strip()] + list(option_aliases_by_option.get(option) or [])
		for candidate_phrase in candidate_phrases:
			normalized_candidate = _normalize_text(candidate_phrase)
			if len(normalized_candidate) < 5:
				continue
			score = difflib.SequenceMatcher(None, normalized_message, normalized_candidate).ratio()
			if score > best_fuzzy_score:
				second_fuzzy_score = best_fuzzy_score
				best_fuzzy_score = score
				best_fuzzy_option = option
				best_fuzzy_mode = "fuzzy_alias" if candidate_phrase != option else "fuzzy_option"
			elif score > second_fuzzy_score:
				second_fuzzy_score = score
	if best_fuzzy_option and best_fuzzy_score >= 0.9 and (best_fuzzy_score - second_fuzzy_score) >= 0.06:
		return best_fuzzy_option, best_fuzzy_mode, float(best_fuzzy_score)
	if len(unique_options) == 1:
		return unique_options[0], "single_option", 0.95

	message_concepts = set(ontology_detect_concepts(normalized_message))
	best_option = ""
	best_score = 0.0
	second_score = 0.0
	best_mode = ""
	for option in unique_options:
		normalized_option = _normalize_text(option)
		score = 0.0
		mode = ""
		candidate_phrases = [normalized_option] + [
			_normalize_text(alias)
			for alias in (option_aliases_by_option.get(option) or [])
			if _normalize_text(alias)
		]
		for candidate in candidate_phrases:
			if normalized_message and (normalized_message in candidate or candidate in normalized_message):
				if 0.86 > score:
					score = 0.86
					mode = "substring"
		if message_concepts:
			for phrase in [option] + list(option_aliases_by_option.get(option) or []):
				option_concepts = set(ontology_detect_concepts(phrase))
				if option_concepts:
					overlap = len(message_concepts & option_concepts) / float(len(option_concepts))
					if overlap > score:
						score = overlap
						mode = "concept_overlap"
		if score > best_score:
			second_score = best_score
			best_score = score
			best_option = option
			best_mode = mode
		elif score > second_score:
			second_score = score
	if best_option and best_score >= 0.6 and (best_score - second_score) >= 0.2:
		return best_option, best_mode or "semantic", float(best_score)
	return "", "", 0.0


def pending_clarification_options_answer(signal_payload: Dict[str, Any]) -> str:
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	if not options:
		return pending_clarification_repeat_answer(signal_payload)
	lines = ["Here are the options I found:"]
	lines.extend(f"- {option}" for option in options[:10])
	return "\n".join(lines)


def pending_clarification_repeat_answer(signal_payload: Dict[str, Any]) -> str:
	question = str(signal_payload.get("user_question") or "").strip()
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	default_message = (
		f"I still need one of these choices before I continue: {_human_join(options[:5])}."
		if options
		else (question or "I still need one more detail before I can continue.")
	)
	return _render_declared_clarification_response(
		signal_payload=signal_payload,
		response_kind="repeat",
		default_message=default_message,
	)


def pending_clarification_meta_answer(signal_payload: Dict[str, Any]) -> str:
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	default_message = (
		f"I'm waiting for one of these choices before I continue: {_human_join(options[:5])}."
		if options
		else "I'm waiting for the missing detail before I continue."
	)
	return _render_declared_clarification_response(
		signal_payload=signal_payload,
		response_kind="meta",
		default_message=default_message,
	)


def pending_clarification_empty_ack_answer(signal_payload: Dict[str, Any]) -> str:
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	default_message = (
		f"I still need one of these choices before I continue: {_human_join(options[:5])}."
		if options
		else (str(signal_payload.get("user_question") or "").strip() or "I still need one more detail before I can continue.")
	)
	return _render_declared_clarification_response(
		signal_payload=signal_payload,
		response_kind="empty_ack",
		default_message=default_message,
	)


def pending_clarification_fallback_stop_answer(signal_payload: Dict[str, Any]) -> str:
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	default_message = (
		f"I'll pause here rather than guess the missing detail. When you come back, please choose one of these directly: {_human_join(options[:5])}."
		if options
		else "I'll pause here rather than guess the missing detail. When you come back, please restate the request with the specific report, area, or period you want."
	)
	return _render_declared_clarification_response(
		signal_payload=signal_payload,
		response_kind="fallback_stop",
		default_message=default_message,
	)


def pending_clarification_discard_answer(signal_payload: Dict[str, Any]) -> str:
	default_message = "Okay, I'll leave that aside. Ask me a new ERP question whenever you're ready."
	return _render_declared_clarification_response(
		signal_payload=signal_payload,
		response_kind="discard",
		default_message=default_message,
	)


def _resolved_slot_payload_value(value: Any) -> Any:
	if isinstance(value, dict):
		out: Dict[str, Any] = {}
		for key, nested_value in value.items():
			clean_key = str(key or "").strip()
			if not clean_key:
				continue
			clean_value = _resolved_slot_payload_value(nested_value)
			if clean_value in ("", [], {}):
				continue
			out[clean_key] = clean_value
		return out
	if isinstance(value, list):
		out: List[Any] = []
		for item in value:
			clean_item = _resolved_slot_payload_value(item)
			if clean_item in ("", [], {}):
				continue
			out.append(clean_item)
		return out
	if isinstance(value, (bool, int, float)):
		return value
	return str(value or "").strip()


def _option_payload_value_by_option(
	payload_by_option: Dict[str, Any],
	matched_option: str,
) -> Any:
	if not isinstance(payload_by_option, dict) or not str(matched_option or "").strip():
		return None
	if matched_option in payload_by_option:
		return payload_by_option.get(matched_option)
	normalized_target = _normalize_text(matched_option)
	for option, value in payload_by_option.items():
		if _normalize_text(option) == normalized_target:
			return value
	return None


def _merge_resolved_slot_payload(
	resolved: Dict[str, Any],
	payload: Dict[str, Any],
) -> Dict[str, Any]:
	merged = dict(resolved or {})
	if not isinstance(payload, dict):
		return merged
	for key, value in payload.items():
		clean_key = str(key or "").strip()
		if not clean_key:
			continue
		clean_value = _resolved_slot_payload_value(value)
		if clean_value in ("", [], {}):
			continue
		if clean_key == "extracted_slots" and isinstance(clean_value, dict):
			existing_slots = merged.get("extracted_slots") if isinstance(merged.get("extracted_slots"), dict) else {}
			merged["extracted_slots"] = {**existing_slots, **clean_value}
			continue
		merged[clean_key] = clean_value
	return merged


def _resolved_slot(
	reason_type: str,
	matched_option: str,
	*,
	internal_details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	if not matched_option:
		return {}
	details = internal_details if isinstance(internal_details, dict) else {}
	resolved_slot_key = str(details.get("resolved_slot_key") or "").strip()
	semantic_slot_name = str(details.get("semantic_slot_name") or "").strip()
	semantic_slot_value_by_option = (
		details.get("semantic_slot_value_by_option")
		if isinstance(details.get("semantic_slot_value_by_option"), dict)
		else {}
	)
	carryover_slot_values = (
		details.get("carryover_slot_values")
		if isinstance(details.get("carryover_slot_values"), dict)
		else {}
	)
	resolved_slot_payload_by_option = (
		details.get("resolved_slot_payload_by_option")
		if isinstance(details.get("resolved_slot_payload_by_option"), dict)
		else {}
	)
	selected_report_by_option = (
		details.get("selected_report_by_option")
		if isinstance(details.get("selected_report_by_option"), dict)
		else {}
	)
	resolved: Dict[str, Any] = {}
	if resolved_slot_key:
		resolved[resolved_slot_key] = matched_option
	elif reason_type == "report_ambiguity":
		resolved["selected_report"] = str(selected_report_by_option.get(matched_option) or matched_option).strip()
	elif reason_type == "capability_ambiguity":
		resolved["selected_business_area"] = matched_option
	elif reason_type in {"time_scope_missing", "time_scope_clarification"}:
		resolved["selected_time_scope"] = matched_option
	elif reason_type.endswith("_basis_missing"):
		resolved["selected_basis"] = matched_option
	else:
		resolved["selected_option"] = matched_option
	semantic_slot_value = _resolved_slot_payload_value(
		_option_payload_value_by_option(semantic_slot_value_by_option, matched_option)
	)
	if semantic_slot_name and semantic_slot_value not in ("", [], {}, None):
		resolved[semantic_slot_name] = semantic_slot_value
	option_payload = _option_payload_value_by_option(resolved_slot_payload_by_option, matched_option)
	if isinstance(option_payload, dict):
		resolved = _merge_resolved_slot_payload(resolved, option_payload)
	for key, value in carryover_slot_values.items():
		clean_key = str(key or "").strip()
		clean_value = _resolved_slot_payload_value(value)
		if clean_key and clean_value not in ("", [], {}, None) and clean_key not in resolved:
			resolved[clean_key] = clean_value
	return resolved


def _clarification_has_structured_resolution_authority(internal_details: Dict[str, Any] | None) -> bool:
	details = internal_details if isinstance(internal_details, dict) else {}
	if str(details.get("resolved_slot_key") or "").strip():
		return True
	if str(details.get("semantic_slot_name") or "").strip():
		slot_values = details.get("semantic_slot_value_by_option")
		if isinstance(slot_values, dict) and slot_values:
			return True
	resolved_payloads = details.get("resolved_slot_payload_by_option")
	if isinstance(resolved_payloads, dict) and resolved_payloads:
		return True
	selected_reports = details.get("selected_report_by_option")
	if isinstance(selected_reports, dict) and selected_reports:
		return True
	carryover_slot_values = details.get("carryover_slot_values")
	if isinstance(carryover_slot_values, dict) and carryover_slot_values:
		return True
	return False


def _option_match_is_embedded_slot_value_in_self_contained_request(
	*,
	reason_type: str,
	message: str,
	matched_option: str,
	matched_by: str,
	option_aliases_by_option: Dict[str, List[str]] | None = None,
	internal_details: Dict[str, Any] | None = None,
) -> bool:
	if not matched_option:
		return False
	if matched_by not in {"exact_token", "exact_token_alias", "substring", "semantic"}:
		return False
	details = internal_details if isinstance(internal_details, dict) else {}
	slot_name = _normalize_text(
		details.get("semantic_slot_name")
		or details.get("resolved_slot_key")
		or ""
	)
	slot_reason = _normalize_text(reason_type)
	if slot_reason not in {"time_scope_missing", "time_scope_clarification"} and slot_name not in {
		"time_scope",
		"requested_time_scope",
		"selected_time_scope",
	}:
		return False
	normalized_message = _normalize_text(message)
	if not normalized_message:
		return False
	candidate_phrases = [matched_option]
	if isinstance(option_aliases_by_option, dict):
		candidate_phrases.extend(option_aliases_by_option.get(matched_option) or [])
	for phrase in candidate_phrases:
		if normalized_message == _normalize_text(phrase):
			return False
	if _message_looks_like_self_contained_governed_business_query(message=message):
		return True
	for phrase in candidate_phrases:
		normalized_phrase = _normalize_text(phrase)
		if not normalized_phrase or not _message_contains_phrase(normalized_message, normalized_phrase):
			continue
		remainder = re.sub(
			r"(^|\s)" + re.escape(normalized_phrase) + r"(\s|$)",
			" ",
			normalized_message,
		)
		if _message_looks_like_self_contained_governed_business_query(message=_normalize_text(remainder)):
			return True
		remainder_business_tokens = [
			token
			for token in _word_tokens(remainder)
			if token not in {
				"a",
				"an",
				"and",
				"for",
				"give",
				"i",
				"in",
				"me",
				"no",
				"number",
				"of",
				"on",
				"one",
				"option",
				"please",
				"show",
				"that",
				"the",
				"this",
				"to",
			}
		]
		if len(remainder_business_tokens) >= 2:
			return True
	return False


def governed_fallback_option(signal_payload: Dict[str, Any]) -> str:
	payload = dict(signal_payload or {})
	for key in ("governed_default_option", "default_option"):
		value = str(payload.get(key) or "").strip()
		if value:
			return value
	internal_details = payload.get("internal_details")
	if isinstance(internal_details, dict):
		for key in ("governed_default_option", "default_option"):
			value = str(internal_details.get(key) or "").strip()
			if value:
				return value
	return ""


def clarification_state_after_unresolved_attempt(state: ClarificationState, signal_payload: Dict[str, Any]) -> ClarificationState:
	if state.has_pending:
		return state.next_attempt()
	return build_pending_clarification_state(signal_payload, attempt_count=1)


def _normalized_values(values: List[str]) -> List[str]:
	out: List[str] = []
	for value in values:
		clean = re.sub(r"\s+", " ", str(value or "").strip().lower())
		if clean and clean not in out:
			out.append(clean)
	return out


def _clarification_structured_options(
	options: List[str],
	internal_details: Dict[str, Any] | None,
) -> List[str]:
	structured_options = [str(value or "").strip() for value in (options or []) if str(value or "").strip()]
	details = internal_details if isinstance(internal_details, dict) else {}
	for key in (
		"resolved_message_by_option",
		"semantic_slot_value_by_option",
		"resolved_slot_payload_by_option",
		"selected_report_by_option",
		"option_aliases_by_option",
	):
		value = details.get(key)
		if not isinstance(value, dict):
			continue
		for option in value.keys():
			clean_option = str(option or "").strip()
			if clean_option:
				structured_options.append(clean_option)
	return list(dict.fromkeys(structured_options))


def _prepared_clarification_options_and_aliases(
	signal_payload: Dict[str, Any],
) -> Tuple[List[str], Dict[str, Any], Dict[str, List[str]]]:
	reason_type = str((signal_payload or {}).get("reason_type") or "").strip()
	raw_options = [
		str(value or "").strip()
		for value in ((signal_payload or {}).get("suggested_options") or [])
		if str(value or "").strip()
	]
	internal_details = (signal_payload or {}).get("internal_details")
	if not isinstance(internal_details, dict):
		internal_details = {}
	option_aliases_by_option = (
		internal_details.get("option_aliases_by_option")
		if isinstance(internal_details.get("option_aliases_by_option"), dict)
		else {}
	)
	options = _clarification_structured_options(raw_options, internal_details)
	if reason_type != "report_ambiguity" or not options:
		return options, internal_details, option_aliases_by_option
	report_option_aliases = _report_option_aliases_by_option(options)
	report_option_slot_values = _report_option_slot_values_by_option(options)
	report_option_report_names = _report_option_report_names_by_option(options)
	merged_option_aliases: Dict[str, List[str]] = {}
	for option in options:
		merged = list(option_aliases_by_option.get(option) or []) + list(report_option_aliases.get(option) or [])
		merged_option_aliases[option] = list(
			dict.fromkeys([str(value or "").strip() for value in merged if str(value or "").strip()])
		)
	merged_internal_details = dict(internal_details)
	payload_slot_values = (
		merged_internal_details.get("semantic_slot_value_by_option")
		if isinstance(merged_internal_details.get("semantic_slot_value_by_option"), dict)
		else {}
	)
	payload_report_names = (
		merged_internal_details.get("selected_report_by_option")
		if isinstance(merged_internal_details.get("selected_report_by_option"), dict)
		else {}
	)
	merged_internal_details["option_aliases_by_option"] = merged_option_aliases
	merged_internal_details["semantic_slot_name"] = (
		"statement_variant"
		if (report_option_slot_values or payload_slot_values)
		else str(merged_internal_details.get("semantic_slot_name") or "")
	)
	merged_internal_details["semantic_slot_value_by_option"] = {
		**report_option_slot_values,
		**payload_slot_values,
	}
	merged_internal_details["selected_report_by_option"] = {
		**report_option_report_names,
		**payload_report_names,
	}
	return options, merged_internal_details, merged_option_aliases


def pending_clarification_message_matches_option(
	message: str,
	signal_payload: Dict[str, Any],
	*,
	min_confidence: float = 0.6,
) -> bool:
	"""Return True when the user reply plausibly answers the active choices.

	This guard lets the front controller keep legitimate short answers like
	"Sales Invoice" or "Last Month" inside the pending clarification flow instead
	of treating them as unrelated fresh ERP requests.
	"""

	options, _internal_details, option_aliases_by_option = _prepared_clarification_options_and_aliases(signal_payload)
	matched_option, _matched_by, confidence = _match_pending_clarification_option(
		message,
		options,
		option_aliases_by_option=option_aliases_by_option,
	)
	return bool(matched_option and float(confidence or 0.0) >= float(min_confidence))


def clarification_continuation_lane(signal_payload: Dict[str, Any]) -> str:
	internal_details = signal_payload.get("internal_details")
	if not isinstance(internal_details, dict):
		return ""
	return str(internal_details.get("continuation_lane") or "").strip()


def clarification_resolved_continuation_message(
	*,
	signal_payload: Dict[str, Any],
	resolved_option: str,
) -> str:
	option = str(resolved_option or "").strip()
	if not option:
		return ""
	internal_details = signal_payload.get("internal_details")
	if not isinstance(internal_details, dict):
		return ""
	resolved_message_by_option = (
		internal_details.get("resolved_message_by_option")
		if isinstance(internal_details.get("resolved_message_by_option"), dict)
		else {}
	)
	if resolved_message_by_option:
		exact_message = str(resolved_message_by_option.get(option) or "").strip()
		if exact_message:
			return exact_message
		normalized_target = _normalize_text(option)
		for key, value in resolved_message_by_option.items():
			if _normalize_text(key) == normalized_target:
				return str(value or "").strip()
	resolved_message_template = str(internal_details.get("resolved_message_template") or "").strip()
	resolved_message_placeholder = str(internal_details.get("resolved_message_placeholder") or "").strip()
	if resolved_message_template and resolved_message_placeholder:
		placeholder = "{" + resolved_message_placeholder + "}"
		if placeholder in resolved_message_template:
			return resolved_message_template.replace(placeholder, option)
	if resolved_message_template:
		template_placeholders = _message_template_placeholders(resolved_message_template)
		if len(template_placeholders) == 1:
			placeholder = "{" + template_placeholders[0] + "}"
			return resolved_message_template.replace(placeholder, option)
	return ""


def _clarification_entity_grain(reason_type: str, internal_details: Dict[str, Any] | None) -> str:
	details = internal_details if isinstance(internal_details, dict) else {}
	entity_grain = str(details.get("entity_grain") or "").strip()
	if entity_grain:
		return entity_grain
	return ""


def _resolve_entity_scope_from_clarification(
	*,
	request_id: str,
	reason_type: str,
	message: str,
	internal_details: Dict[str, Any] | None,
) -> Dict[str, Any]:
	entity_grain = _clarification_entity_grain(reason_type, internal_details)
	reply_text = str(message or "").strip()
	if not entity_grain or not reply_text:
		return {}
	details = internal_details if isinstance(internal_details, dict) else {}
	normalized_slots = normalize_master_data_lookup_slots(
		message=message,
		entity_grain=entity_grain,
		preferred_slots={
			"lookup_mode": str(details.get("lookup_mode") or "").strip(),
		},
	)
	search_text = str(normalized_slots.get("lookup_search_text") or "").strip() or reply_text
	lookup_mode = str(normalized_slots.get("lookup_mode") or details.get("lookup_mode") or "").strip()
	payload = resolve_entity_reference_from_message(
		request_id=f"{request_id}-clarification-entity",
		entity_grain=entity_grain,
		message=message,
		lookup_mode=lookup_mode,
		search_text=search_text,
	)
	return dict(payload) if isinstance(payload, dict) else {}


def _same_pending_clarification(
	*,
	compiler_contract: Any,
	signal_payload: Dict[str, Any],
) -> bool:
	pending_reason_type = str(signal_payload.get("reason_type") or "").strip()
	compiler_reason_type = str(getattr(compiler_contract, "clarification_reason_type", "") or "").strip()
	if not pending_reason_type or compiler_reason_type != pending_reason_type:
		return False
	compiler_details = getattr(compiler_contract, "clarification_details", None)
	if not isinstance(compiler_details, dict):
		return False
	pending_options = _normalized_values(
		[
			str(value or "").strip()
			for value in (signal_payload.get("suggested_options") or [])
			if str(value or "").strip()
		]
	)
	if not pending_options:
		return False
	candidate_values: List[str] = []
	for key in ("report_candidates", "capability_candidates", "suggested_options"):
		values = compiler_details.get(key)
		if isinstance(values, list):
			candidate_values = [str(value or "").strip() for value in values if str(value or "").strip()]
			if candidate_values:
				break
	if not candidate_values:
		return False
	return _normalized_values(candidate_values) == pending_options


def _semantic_new_request_detected(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	signal_payload: Dict[str, Any],
) -> bool:
	result = interpret_fresh_query_semantically(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		recent_messages=[],
	)
	interpretation = getattr(result, "interpretation", None)
	if interpretation is None:
		return False
	if not bool(list(getattr(interpretation, "candidate_capability_ids", []) or []) or list(
		getattr(interpretation, "candidate_reports", []) or []
	)):
		return False
	compiler_outcome = compile_fresh_query(
		request_id=request_id,
		session_id=session_id,
		interpretation=interpretation,
		response_policy={"analysis_level": "none"},
	)
	compiler_contract = getattr(compiler_outcome, "compiler_contract", None)
	if compiler_contract is None:
		return False
	decision = str(getattr(compiler_contract, "decision", "") or "").strip()
	if decision not in {"execute", "clarify"}:
		return False
	if decision == "clarify" and _same_pending_clarification(
		compiler_contract=compiler_contract,
		signal_payload=signal_payload,
	):
		return False
	return True


def _shared_frontdoor_business_request_detected(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	grounded_turn: Dict[str, Any] | None = None,
	include_master_data: bool = True,
) -> bool:
	if maybe_build_governed_kpi_frontdoor_response(
		request_id=request_id,
		message=message,
	):
		return True
	if maybe_build_governed_kpi_value_frontdoor_response(
		request_id=request_id,
		message=message,
		grounded_turn=grounded_turn,
	):
		return True
	if maybe_build_governed_composite_frontdoor_response(
		request_id=request_id,
		message=message,
	):
		return True
	if include_master_data:
		master_data_frontdoor = assess_master_data_frontdoor_request(
			request_id=request_id,
			message=message,
		)
		assessment_contract = (
			master_data_frontdoor.get("assessment_contract")
			if isinstance(master_data_frontdoor, dict)
			else None
		)
		if assessment_contract is not None and str(getattr(assessment_contract, "status", "") or "").strip() in {
			"resolved",
			"clarification_required",
		}:
			return True
	try:
		frontdoor_semantic_result = interpret_front_door_semantically(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=[],
			grounded_context_available=bool(grounded_turn),
		)
	except Exception:
		frontdoor_semantic_result = None
	if frontdoor_semantic_result is None:
		return False
	status = str(getattr(frontdoor_semantic_result, "status", "") or "").strip()
	intent = getattr(frontdoor_semantic_result, "intent", None)
	intent_class = str(getattr(intent, "intent_class", "") or "").strip()
	if status not in {"accepted", "guardrailed_to_route_onward"}:
		return False
	if intent_class in {
		"",
		"greeting",
		"thanks",
		"acknowledgement",
		"closure_signoff",
		"low_signal_non_business",
		"capability_question",
		"compound_request_clarification",
		"master_data_grain_clarification",
	}:
		return False
	if intent_class != "route_onward":
		return True
	return _message_looks_like_self_contained_governed_business_query(message=message)


def _frontdoor_new_request_detected(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	grounded_turn: Dict[str, Any] | None = None,
) -> bool:
	return _shared_frontdoor_business_request_detected(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		grounded_turn=grounded_turn,
		include_master_data=True,
	)


def _structured_frontdoor_clarification_breakout_detected(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	grounded_turn: Dict[str, Any] | None = None,
) -> bool:
	if _semantic_slot_alias_matches("listing_view", message):
		return True
	if _semantic_slot_alias_matches("statement_variant", message):
		return True
	if any(_message_contains_phrase(message, alias) for alias in _financial_statement_family_aliases()):
		return True
	return _shared_frontdoor_business_request_detected(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		grounded_turn=grounded_turn,
		include_master_data=False,
	)


def _master_data_clarification_breakout_detected(
	*,
	request_id: str,
	message: str,
	signal_payload: Dict[str, Any],
) -> bool:
	def _entity_grain_aliases(entity_grain: str) -> List[str]:
		clean_grain = _normalize_text(entity_grain)
		if not clean_grain:
			return []
		aliases = {
			clean_grain.replace("_", " "),
			_normalize_text(entity_grain_display_label(clean_grain, plural=False)),
			_normalize_text(entity_grain_display_label(clean_grain, plural=True)),
		}
		for entry in list_semantic_resolution_alias_entries("entity_grain"):
			if not isinstance(entry, dict):
				continue
			if _normalize_text(entry.get("canonical_value")) != clean_grain:
				continue
			for alias in entry.get("aliases") or []:
				normalized_alias = _normalize_text(alias)
				if normalized_alias:
					aliases.add(normalized_alias)
		return [alias for alias in aliases if alias]

	internal_details = signal_payload.get("internal_details") if isinstance(signal_payload, dict) else {}
	if not isinstance(internal_details, dict):
		internal_details = {}
	pending_entity_grain = _normalize_text(
		internal_details.get("entity_grain")
		or (
			internal_details.get("carryover_slot_values", {}).get("entity_grain")
			if isinstance(internal_details.get("carryover_slot_values"), dict)
			else ""
		)
	)
	pending_lookup_mode = _normalize_text(
		internal_details.get("lookup_mode")
		or (
			internal_details.get("carryover_slot_values", {}).get("lookup_mode")
			if isinstance(internal_details.get("carryover_slot_values"), dict)
			else ""
		)
	)
	pending_lookup_search_text = _normalize_text(
		internal_details.get("lookup_search_text")
		or (
			internal_details.get("carryover_slot_values", {}).get("lookup_search_text")
			if isinstance(internal_details.get("carryover_slot_values"), dict)
			else ""
		)
	)
	if not pending_entity_grain:
		return False
	master_data_frontdoor = assess_master_data_frontdoor_request(
		request_id=request_id,
		message=message,
	)
	assessment_contract = (
		master_data_frontdoor.get("assessment_contract")
		if isinstance(master_data_frontdoor, dict)
		else None
	)
	if assessment_contract is None:
		return False
	status = _normalize_text(getattr(assessment_contract, "status", ""))
	if status not in {"resolved", "clarification_required"}:
		return False
	request_entity_grain = _normalize_text(getattr(assessment_contract, "entity_grain", ""))
	request_lookup_mode = _normalize_text(getattr(assessment_contract, "request_mode", ""))
	request_lookup_search_text = _normalize_text(getattr(assessment_contract, "lookup_search_text", ""))
	supported_entity_grains = [
		_normalize_text(value)
		for value in (getattr(assessment_contract, "supported_entity_grains", []) or [])
		if _normalize_text(value)
	]
	ambiguity_reason_type = _normalize_text(getattr(assessment_contract, "ambiguity_reason_type", ""))
	if request_entity_grain and request_entity_grain != pending_entity_grain:
		return True
	if (
		request_entity_grain
		and request_entity_grain == pending_entity_grain
		and pending_lookup_mode
		and request_lookup_mode
		and request_lookup_mode != pending_lookup_mode
	):
		return True
	if (
		request_entity_grain
		and request_entity_grain == pending_entity_grain
		and pending_lookup_mode
		and request_lookup_mode
		and request_lookup_mode == pending_lookup_mode
		and pending_lookup_search_text
		and request_lookup_search_text
		and request_lookup_search_text != pending_lookup_search_text
	):
		return True
	if (
		status == "clarification_required"
		and ambiguity_reason_type == "master_data_entity_grain_missing"
		and request_lookup_mode
	):
		explicit_supported_grains = [
			grain
			for grain in supported_entity_grains
			if grain
			and grain != pending_entity_grain
			and any(_message_contains_phrase(message, alias) for alias in _entity_grain_aliases(grain))
		]
		if len(explicit_supported_grains) == 1:
			return True
	return False


def resolve_pending_clarification_response(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	signal_payload: Dict[str, Any],
	clarification_attempt_count: int = 0,
	max_attempts: int = 3,
	grounded_turn: Dict[str, Any] | None = None,
	control_evidence_payload: Dict[str, Any] | None = None,
) -> Any:
	stage = str(signal_payload.get("stage") or "").strip()
	reason_type = str(signal_payload.get("reason_type") or "").strip()
	user_question = str(signal_payload.get("user_question") or "").strip()
	options, internal_details, option_aliases_by_option = _prepared_clarification_options_and_aliases(signal_payload)
	continuation_lane = (
		str(internal_details.get("continuation_lane") or "").strip()
		if isinstance(internal_details, dict)
		else ""
	)
	control_evidence = _control_evidence_payload(message, payload=control_evidence_payload)
	matched_option, matched_by, confidence = _match_pending_clarification_option(
		message,
		options,
		option_aliases_by_option=option_aliases_by_option,
	)
	entity_scope_resolution = _resolve_entity_scope_from_clarification(
		request_id=request_id,
		reason_type=reason_type,
		message=message,
		internal_details=internal_details if isinstance(internal_details, dict) else {},
	)
	if str(entity_scope_resolution.get("resolution_status") or "").strip() == "resolved":
		resolved_entity = (
			entity_scope_resolution.get("resolved_entity")
			if isinstance(entity_scope_resolution.get("resolved_entity"), dict)
			else {}
		)
		resolved_entity_label = str(
			resolved_entity.get("entity_label")
			or resolved_entity.get("entity_key")
			or ""
		).strip()
		resolution_source = str(resolved_entity.get("resolution_source") or "").strip()
		if resolved_entity_label:
			entity_matched_by = "entity_reference_fuzzy"
			entity_confidence = 0.95
			if resolution_source in {"exact_name", "exact_display"}:
				entity_matched_by = "entity_reference_exact"
				entity_confidence = 1.0
			return build_clarification_resolution_contract(
				request_id=request_id,
				session_id=session_id,
				pending_stage=stage,
				pending_reason_type=reason_type,
				pending_user_question=user_question,
				pending_suggested_options=options,
				decision="resolved_option",
				resolved_option=resolved_entity_label,
				matched_by=entity_matched_by,
				confidence=entity_confidence,
				reason="The user supplied a valid entity reference for the pending scope clarification.",
				resolved_slot=_resolved_slot(
					reason_type,
					resolved_entity_label,
					internal_details=internal_details if isinstance(internal_details, dict) else {},
				),
				clarification_attempt_count=int(max(0, clarification_attempt_count)),
				is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
			)
	if str(control_evidence.get("action_id") or "").strip() == "show_pending_options":
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="show_options",
			matched_by="shared_control_evidence",
			confidence=0.9,
			reason="The shared conversation-control evidence indicates the user asked to review the available options before choosing one.",
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
			internal_details={
				"control_evidence_class": str(control_evidence.get("evidence_class") or "").strip(),
				"control_action_id": str(control_evidence.get("action_id") or "").strip(),
			},
		)
	embedded_business_message = str(control_evidence.get("embedded_business_message") or "").strip()
	if str(control_evidence.get("action_id") or "").strip() == "override_with_new_request" and embedded_business_message:
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="new_request",
			confidence=0.92,
			reason="The shared conversation-control evidence indicates the user explicitly abandoned the current clarification and started a new ERP request.",
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
			internal_details={
				"override_business_message": embedded_business_message,
				"control_evidence_class": str(control_evidence.get("evidence_class") or "").strip(),
				"control_action_id": str(control_evidence.get("action_id") or "").strip(),
			},
		)
	if str(control_evidence.get("action_id") or "").strip() == "abandon_current_branch":
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="abandon_current_branch",
			matched_by="shared_control_evidence",
			confidence=0.9,
			reason="The shared conversation-control evidence indicates the user explicitly abandoned the current clarification without starting a replacement request.",
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
			internal_details={
				"control_evidence_class": str(control_evidence.get("evidence_class") or "").strip(),
				"control_action_id": str(control_evidence.get("action_id") or "").strip(),
			},
		)
	artifact_boundary_option_match = bool(
		continuation_lane == "artifact_boundary"
		and matched_option
		and float(confidence or 0.0) >= 0.6
		and isinstance(internal_details, dict)
		and isinstance(internal_details.get("resolved_message_by_option"), dict)
	)
	frontdoor_structured_option_match = bool(
		continuation_lane == "front_door"
		and matched_option
		and float(confidence or 0.0) >= 0.6
		and _clarification_has_structured_resolution_authority(
			internal_details if isinstance(internal_details, dict) else {},
		)
	)
	accepted_direct_match_modes = {"exact", "exact_alias", "exact_token", "exact_token_alias", "single_option"}
	authoritative_option_resolution = bool(
		matched_option
		and (
			matched_by in accepted_direct_match_modes
			or artifact_boundary_option_match
			or frontdoor_structured_option_match
		)
	)
	option_match_should_yield_to_new_request = _option_match_is_embedded_slot_value_in_self_contained_request(
		reason_type=reason_type,
		message=message,
		matched_option=matched_option,
		matched_by=matched_by,
		option_aliases_by_option=option_aliases_by_option,
		internal_details=internal_details if isinstance(internal_details, dict) else {},
	)
	allow_breakout_crosscheck = bool(
		not authoritative_option_resolution
		or option_match_should_yield_to_new_request
	)
	empty_ack = _looks_like_empty_ack(message)
	new_request_detected = False if empty_ack else (
		_master_data_clarification_breakout_detected(
			request_id=request_id,
			message=message,
			signal_payload=signal_payload,
		) or (
			allow_breakout_crosscheck
			and _structured_frontdoor_clarification_breakout_detected(
				request_id=request_id,
				session_id=session_id,
				user_id=user_id,
				site_name=site_name,
				message=message,
				grounded_turn=grounded_turn,
			)
		) or (
			allow_breakout_crosscheck
			and (
				_semantic_new_request_detected(
					request_id=request_id,
					session_id=session_id,
					user_id=user_id,
					site_name=site_name,
					message=message,
					signal_payload=signal_payload,
				)
				or _frontdoor_new_request_detected(
					request_id=request_id,
					session_id=session_id,
					user_id=user_id,
					site_name=site_name,
					message=message,
					grounded_turn=grounded_turn,
				)
			)
		)
	)
	if (
		not new_request_detected
		and matched_option
		and matched_by not in {"exact", "exact_alias", "single_option"}
		and _message_looks_like_self_contained_governed_business_query(message=message)
	):
		new_request_detected = True
	if matched_option and (
		not (new_request_detected and option_match_should_yield_to_new_request)
		and (
			matched_by in accepted_direct_match_modes
			or artifact_boundary_option_match
			or frontdoor_structured_option_match
			or not new_request_detected
		)
	):
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="resolved_option",
			resolved_option=matched_option,
			matched_by=matched_by,
			confidence=confidence,
			reason="The user selected one of the pending clarification options.",
			resolved_slot=_resolved_slot(
				reason_type,
				matched_option,
				internal_details=internal_details if isinstance(internal_details, dict) else {},
			),
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
		)
	if _looks_like_option_list_request(message):
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="show_options",
			matched_by="clarification_helper_request",
			confidence=0.85,
			reason="The user asked to see the available clarification options before choosing one.",
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
		)
	if new_request_detected:
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="new_request",
			confidence=0.8,
			reason="A semantic fresh-query cross-check indicates the user started a new ERP request and should continue through the main lanes.",
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
		)
	if _looks_like_meta_question(message):
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="meta_question",
			matched_by="question_shape",
			confidence=0.7,
			reason="The user asked about the pending clarification itself rather than selecting an option.",
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
		)
	if empty_ack:
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="empty_ack",
			matched_by="short_non_business_turn",
			confidence=0.65,
			reason="The user acknowledged the clarification but did not provide a resolvable option yet.",
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
		)
	return build_clarification_resolution_contract(
		request_id=request_id,
		session_id=session_id,
		pending_stage=stage,
		pending_reason_type=reason_type,
		pending_user_question=user_question,
		pending_suggested_options=options,
		decision="reask_pending_clarification",
		confidence=0.0,
		reason="The user did not answer the pending clarification with a resolvable option or new substantive ERP request.",
		clarification_attempt_count=int(max(0, clarification_attempt_count)),
		is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
	)
