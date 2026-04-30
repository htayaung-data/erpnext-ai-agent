from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	build_clarification_signal_contract,
	build_master_data_frontdoor_assessment_contract,
)
from ai_assistant_ui.qwen_chat.clarification_translation import translate_clarification_signal
from ai_assistant_ui.qwen_chat.entity_reference_resolution import (
	infer_lookup_mode_from_message,
	infer_entity_grains_from_message,
	normalize_master_data_lookup_slots,
	resolve_entity_reference_from_message,
)
from ai_assistant_ui.qwen_chat.governed_scope_registry import (
	canonical_master_data_entity_grain,
	list_active_master_data_scope_activations,
	master_data_scope_activation,
)
from ai_assistant_ui.qwen_chat.metadata import (
	entity_grain_display_label,
	ontology_detect_concepts,
)


_MASTER_DATA_COMPATIBLE_CONCEPTS = {
	"customer",
	"supplier",
	"product",
	"territory",
	"warehouse",
}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _frontdoor_slot_text(slots: Dict[str, Any] | None, key: str) -> str:
	if not isinstance(slots, dict):
		return ""
	return _clean_text(slots.get(key))


def _master_data_blocking_business_concepts(message: str) -> List[str]:
	concepts = [
		_clean_text(value)
		for value in ontology_detect_concepts(message)
		if _clean_text(value)
	]
	return [
		value
		for value in list(dict.fromkeys(concepts))
		if value not in _MASTER_DATA_COMPATIBLE_CONCEPTS
	]


def _active_master_data_grains(*, request_mode: str = "") -> List[str]:
	return list(
		dict.fromkeys(
			_clean_text(item.get("entity_grain"))
			for item in list_active_master_data_scope_activations(request_mode=request_mode)
			if _clean_text(item.get("entity_grain"))
		)
	)


def _master_data_option_label(entity_grain: str) -> str:
	return entity_grain_display_label(entity_grain, plural=True).title()


def _message_for_option(*, request_mode: str, entity_grain: str, lookup_search_text: str) -> str:
	singular = entity_grain_display_label(entity_grain, plural=False) or entity_grain
	plural = entity_grain_display_label(entity_grain, plural=True) or f"{entity_grain}s"
	if request_mode == "candidate_resolution" and _clean_text(lookup_search_text):
		return f'do u have {singular} name similar to "{lookup_search_text}"'
	if request_mode == "profile_target" and _clean_text(lookup_search_text):
		return f"tell me more about {singular} {_clean_text(lookup_search_text)}"
	return f"give me some {singular} list"


def _clarification_question(*, request_mode: str, active_grains: List[str]) -> str:
	labels = [
		entity_grain_display_label(value, plural=True)
		for value in active_grains
		if _clean_text(entity_grain_display_label(value, plural=True))
	]
	labels = list(dict.fromkeys(labels))
	if not labels:
		return "Which master-data group would you like?"
	if request_mode == "candidate_resolution":
		if len(labels) == 2:
			return f"I can check {labels[0]} or {labels[1]} for that name. Which one do you mean?"
		return f"I can check {' or '.join(labels)} for that name. Which one do you mean?"
	if len(labels) == 2:
		return f"I can help with {labels[0]} or {labels[1]}. Which one would you like?"
	return f"I can help with {' or '.join(labels)}. Which one would you like?"


def _entity_candidate_question(*, entity_grain: str, lookup_search_text: str, option_count: int) -> str:
	singular = entity_grain_display_label(entity_grain, plural=False) or entity_grain or "item"
	search_suffix = f' for "{_clean_text(lookup_search_text)}"' if _clean_text(lookup_search_text) else ""
	if option_count <= 1:
		return f"I found one {singular}{search_suffix}. Is this the one you mean?"
	return f"I found more than one {singular}{search_suffix}. Which one do you mean?"


def _entity_candidate_resolved_slot_key(entity_grain: str) -> str:
	grain = _clean_text(entity_grain)
	if not grain:
		return "selected_entity"
	return f"selected_{grain}"


def maybe_build_master_data_entity_reference_clarification(
	*,
	request_id: str,
	message: str,
	assessment_contract: Any,
) -> Dict[str, Any]:
	if assessment_contract is None:
		return {}
	if str(getattr(assessment_contract, "status", "") or "").strip() != "resolved":
		return {}
	entity_grain = _clean_text(getattr(assessment_contract, "entity_grain", ""))
	request_mode = _clean_text(getattr(assessment_contract, "request_mode", ""))
	if not entity_grain or request_mode != "candidate_resolution":
		return {}
	lookup_search_text = _clean_text(getattr(assessment_contract, "lookup_search_text", ""))
	resolution_payload = resolve_entity_reference_from_message(
		request_id=f"{request_id}-entity-reference",
		entity_grain=entity_grain,
		message=message,
		lookup_mode=request_mode,
		search_text=lookup_search_text,
	)
	resolution_status = _clean_text(resolution_payload.get("resolution_status"))
	candidate_entities = [
		dict(item)
		for item in (resolution_payload.get("candidate_entities") or [])
		if isinstance(item, dict)
	]
	option_labels = list(
		dict.fromkeys(
			_clean_text(item.get("entity_label") or item.get("entity_key"))
			for item in candidate_entities
			if _clean_text(item.get("entity_label") or item.get("entity_key"))
		)
	)
	if resolution_status not in {"ambiguous", "not_found"} or not option_labels:
		return {
			"entity_reference_resolution": resolution_payload,
		}
	carryover_slot_values = {
		"entity_grain": entity_grain,
		"lookup_mode": request_mode,
		"lookup_search_text": lookup_search_text,
	}
	clarification_signal = build_clarification_signal_contract(
		request_id=request_id,
		stage="front_door",
		reason_type="entity_scope_missing",
		user_question=_entity_candidate_question(
			entity_grain=entity_grain,
			lookup_search_text=lookup_search_text,
			option_count=len(option_labels),
		),
		suggested_options=option_labels,
		internal_reason="The request matched multiple governed entity candidates and needs a concrete entity selection.",
		internal_details={
			"continuation_lane": "front_door",
			"entity_grain": entity_grain,
			"lookup_mode": request_mode,
			"inline_options_on_first_turn": True,
			"inline_option_heading": "Here are the options I found:",
			"resolved_slot_key": _entity_candidate_resolved_slot_key(entity_grain),
			"option_aliases_by_option": {
				option: [option]
				for option in option_labels
			},
			"carryover_slot_values": {
				key: value
				for key, value in carryover_slot_values.items()
				if _clean_text(value)
			},
		},
	)
	return {
		"clarification_signal": clarification_signal,
		"entity_reference_resolution": resolution_payload,
	}


def assess_master_data_frontdoor_request(
	*,
	request_id: str,
	message: str,
	frontdoor_extracted_slots: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	typed_slots = dict(frontdoor_extracted_slots or {}) if isinstance(frontdoor_extracted_slots, dict) else {}
	lookup_mode = _frontdoor_slot_text(typed_slots, "lookup_mode") or _clean_text(infer_lookup_mode_from_message(message))
	all_active_grains = _active_master_data_grains()
	active_grains = _active_master_data_grains(request_mode=lookup_mode)
	if not lookup_mode:
		return {
			"assessment_contract": build_master_data_frontdoor_assessment_contract(
				request_id=request_id,
				status="not_applicable",
				supported_entity_grains=all_active_grains,
			),
			"clarification_signal": None,
		}
	blocking_concepts = _master_data_blocking_business_concepts(message)
	if blocking_concepts:
		return {
			"assessment_contract": build_master_data_frontdoor_assessment_contract(
				request_id=request_id,
				status="not_applicable",
				request_mode=lookup_mode,
				supported_entity_grains=all_active_grains,
				internal_details={
					"blocked_by_business_concepts": list(blocking_concepts),
					"frontdoor_extracted_slots": dict(typed_slots),
					"source": "frontdoor_master_data_assessment",
				},
			),
			"clarification_signal": None,
		}

	inferred_message_grains = [
		canonical_master_data_entity_grain(grain)
		for grain in infer_entity_grains_from_message(message)
		if _clean_text(canonical_master_data_entity_grain(grain))
	]
	explicit_grains: List[str] = []
	unsupported_explicit_grains: List[str] = []
	raw_typed_entity_grain = _frontdoor_slot_text(typed_slots, "entity_grain")
	typed_entity_grain = canonical_master_data_entity_grain(raw_typed_entity_grain) if raw_typed_entity_grain else ""
	if typed_entity_grain in all_active_grains:
		explicit_grains.append(typed_entity_grain)
	elif raw_typed_entity_grain:
		unsupported_explicit_grains.append(raw_typed_entity_grain)
	if not raw_typed_entity_grain:
		explicit_grains.extend(
			[
				grain
				for grain in inferred_message_grains
				if _clean_text(grain) in all_active_grains
			]
		)
		unsupported_explicit_grains.extend(
			[
				grain
				for grain in inferred_message_grains
				if _clean_text(grain) and _clean_text(grain) not in all_active_grains
			]
		)
	explicit_grains = list(dict.fromkeys([_clean_text(value) for value in explicit_grains if _clean_text(value)]))
	unsupported_explicit_grains = list(
		dict.fromkeys([_clean_text(value) for value in unsupported_explicit_grains if _clean_text(value)])
	)
	if len(explicit_grains) == 0 and len(unsupported_explicit_grains) == 1 and all_active_grains:
		requested_entity_grain = unsupported_explicit_grains[0]
		assessment = build_master_data_frontdoor_assessment_contract(
			request_id=request_id,
			status="clarification_required",
			entity_grain=requested_entity_grain,
			request_mode=lookup_mode,
			supported_entity_grains=all_active_grains,
			ambiguity_reason_type="master_data_scope_unsupported",
			internal_details={
				"requested_entity_grain": requested_entity_grain,
				"supported_entity_grains": list(all_active_grains),
				"frontdoor_extracted_slots": dict(typed_slots),
				"source": "frontdoor_master_data_assessment",
			},
		)
		clarification_signal = translate_clarification_signal(
			request_id=request_id,
			compiler_reason="unsupported master-data scope",
			compiler_reason_type="master_data_scope_unsupported",
			compiler_details={
				"requested_entity_grain": requested_entity_grain,
				"supported_entity_grains": list(all_active_grains),
			},
		)
		return {
			"assessment_contract": assessment,
			"clarification_signal": clarification_signal,
		}
	if len(explicit_grains) == 1:
		entity_grain = explicit_grains[0]
		activation = master_data_scope_activation(entity_grain)
		if not activation or lookup_mode not in [
			_clean_text(value) for value in (activation.get("allowed_lookup_modes") or [])
		]:
			return {
				"assessment_contract": build_master_data_frontdoor_assessment_contract(
					request_id=request_id,
					status="not_applicable",
					entity_grain=entity_grain,
					request_mode=lookup_mode,
					supported_entity_grains=all_active_grains,
				),
				"clarification_signal": None,
			}
		normalized_slots = normalize_master_data_lookup_slots(
			message=message,
			entity_grain=entity_grain,
			preferred_slots=typed_slots,
		)
		resolved_request_mode = _clean_text(normalized_slots.get("lookup_mode")) or lookup_mode
		resolved_lookup_projection = _clean_text(normalized_slots.get("lookup_projection"))
		resolved_lookup_search_text = _clean_text(normalized_slots.get("lookup_search_text"))
		assessment = build_master_data_frontdoor_assessment_contract(
			request_id=request_id,
			status="resolved",
			scope_id=_clean_text(activation.get("scope_id")),
			entity_grain=entity_grain,
			request_mode=resolved_request_mode,
			lookup_projection=resolved_lookup_projection,
			lookup_search_text=resolved_lookup_search_text,
			capability_id=_clean_text(activation.get("capability_id")),
			report_name=_clean_text(activation.get("report_name")),
			allowed_lookup_modes=[
				_clean_text(value)
				for value in (activation.get("allowed_lookup_modes") or [])
				if _clean_text(value)
			],
			supported_entity_grains=active_grains,
			internal_details={
				"lookup_limit": int(max(0, normalized_slots.get("lookup_limit") or 0)),
				"scope_id": _clean_text(activation.get("scope_id")),
				"capability_id": _clean_text(activation.get("capability_id")),
				"report_name": _clean_text(activation.get("report_name")),
				"allowed_lookup_modes": [
					_clean_text(value)
					for value in (activation.get("allowed_lookup_modes") or [])
					if _clean_text(value)
				],
				"frontdoor_extracted_slots": dict(typed_slots),
				"source": "frontdoor_master_data_assessment",
			},
		)
		return {
			"assessment_contract": assessment,
			"clarification_signal": None,
		}

	if lookup_mode not in {"directory_list", "candidate_resolution"} or len(active_grains) < 2:
		return {
			"assessment_contract": build_master_data_frontdoor_assessment_contract(
				request_id=request_id,
				status="not_applicable",
				request_mode=lookup_mode,
				supported_entity_grains=all_active_grains,
			),
			"clarification_signal": None,
		}

	search_text = _frontdoor_slot_text(typed_slots, "lookup_search_text")
	projection = _frontdoor_slot_text(typed_slots, "lookup_projection")
	for entity_grain in active_grains:
		normalized_slots = normalize_master_data_lookup_slots(
			message=message,
			entity_grain=entity_grain,
			preferred_slots={
				"lookup_mode": lookup_mode,
				"lookup_projection": projection,
				"lookup_search_text": search_text,
			},
		)
		search_text = search_text or _clean_text(normalized_slots.get("lookup_search_text"))
		projection = projection or _clean_text(normalized_slots.get("lookup_projection"))

	assessment = build_master_data_frontdoor_assessment_contract(
		request_id=request_id,
		status="clarification_required",
		request_mode=lookup_mode,
		lookup_projection=projection,
		lookup_search_text=search_text,
		supported_entity_grains=active_grains,
		ambiguity_reason_type="master_data_entity_grain_missing",
		internal_details={
			"frontdoor_extracted_slots": dict(typed_slots),
			"source": "frontdoor_master_data_assessment",
		},
	)
	suggested_options = [_master_data_option_label(value) for value in active_grains]
	resolved_message_by_option = {
		_master_data_option_label(value): _message_for_option(
			request_mode=lookup_mode,
			entity_grain=value,
			lookup_search_text=search_text,
		)
		for value in active_grains
	}
	option_aliases_by_option = {
		_master_data_option_label(value): [
			_clean_text(_master_data_option_label(value)),
			_clean_text(entity_grain_display_label(value, plural=False)),
			_clean_text(entity_grain_display_label(value, plural=True)),
		]
		for value in active_grains
	}
	semantic_slot_value_by_option = {
		_master_data_option_label(value): value
		for value in active_grains
		if _clean_text(value)
	}
	carryover_slot_values = {
		"lookup_mode": _clean_text(lookup_mode),
		"lookup_projection": _clean_text(projection),
		"lookup_search_text": _clean_text(search_text),
	}
	clarification_signal = build_clarification_signal_contract(
		request_id=request_id,
		stage="front_door",
		reason_type="master_data_entity_grain_missing",
		user_question=_clarification_question(
			request_mode=lookup_mode,
			active_grains=active_grains,
		),
		suggested_options=suggested_options,
		internal_reason="The request is master-data navigation, but the entity grain is still ambiguous.",
		internal_details={
			"continuation_lane": "front_door",
			"resolved_message_by_option": resolved_message_by_option,
			"option_aliases_by_option": option_aliases_by_option,
			"semantic_slot_name": "entity_grain",
			"semantic_slot_value_by_option": semantic_slot_value_by_option,
			"carryover_slot_values": {
				key: value
				for key, value in carryover_slot_values.items()
				if _clean_text(value)
			},
			"supported_entity_grains": list(active_grains),
			"request_mode": lookup_mode,
			"lookup_search_text": search_text,
		},
	)
	return {
		"assessment_contract": assessment,
		"clarification_signal": clarification_signal,
	}
