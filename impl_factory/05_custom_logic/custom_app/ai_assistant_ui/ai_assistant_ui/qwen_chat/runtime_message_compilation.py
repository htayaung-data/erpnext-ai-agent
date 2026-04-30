from __future__ import annotations

import re
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.recent_focus_support import (
	build_recent_focus_affordance_contract_from_snapshot,
	recent_focus_runtime_route_selection,
)


_CONTEXTUAL_BREAKOUT_ENTITY_NOUNS = {
	"customer": "customer",
	"supplier": "supplier",
	"item": "item",
	"sales_invoice": "sales invoice",
	"purchase_invoice": "purchase invoice",
	"sales_order": "sales order",
	"purchase_order": "purchase order",
	"delivery_note": "delivery note",
	"payment_entry": "payment entry",
	"purchase_receipt": "purchase receipt",
}


def clean_runtime_text(value: Any) -> str:
	return str(value or "").strip()


def normalize_runtime_text(value: Any) -> str:
	return " ".join(clean_runtime_text(value).lower().split())


def _ordinal_reference_index(message: str) -> int:
	normalized = normalize_runtime_text(message)
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
	number_patterns = (
		r"\b(?:rank|row|number|no|no\.|#)\s*(\d{1,2})\b",
		r"\b(\d{1,2})(?:st|nd|rd|th)\b",
	)
	for pattern in number_patterns:
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


def _candidate_rank_value(item: Dict[str, Any], fallback_index: int) -> int:
	for key in ("rank", "row_rank", "position"):
		try:
			value = int(item.get(key) or 0)
		except (TypeError, ValueError):
			value = 0
		if value > 0:
			return value
	return fallback_index + 1


def _entity_reference_from_candidate(item: Dict[str, Any]) -> Dict[str, str]:
	entity_type = clean_runtime_text(item.get("entity_type"))
	entity_key = clean_runtime_text(item.get("code") or item.get("entity_key") or item.get("name"))
	entity_label = clean_runtime_text(item.get("name") or item.get("entity_label") or entity_key)
	if not entity_type or not (entity_key or entity_label):
		return {}
	return {
		"entity_type": entity_type,
		"entity_key": entity_key or entity_label,
		"entity_label": entity_label or entity_key,
	}


def looks_like_contextual_detail_request(message: str) -> bool:
	normalized = normalize_runtime_text(message)
	if not normalized:
		return False
	detail_prefixes = (
		"tell me more",
		"show me details",
		"show details",
		"give me more info",
		"give me more information",
		"show me more",
		"more detail",
		"more details",
	)
	return normalized.startswith(detail_prefixes) or normalized in {"details", "detail"}


def grounded_entity_reference(
	*,
	grounded_turn: Dict[str, Any],
	artifact_payload: Dict[str, Any],
	raw_message: str = "",
) -> Dict[str, str]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	candidates: list[Dict[str, str]] = []
	for index, item in enumerate(turn.get("known_entities") or []):
		if not isinstance(item, dict):
			continue
		candidate = _entity_reference_from_candidate(item)
		if candidate:
			candidate["rank"] = str(_candidate_rank_value(item, index))
			candidates.append(candidate)
	ordinal_index = _ordinal_reference_index(raw_message)
	if ordinal_index >= 0:
		for item in candidates:
			try:
				rank_value = int(item.get("rank") or 0)
			except (TypeError, ValueError):
				rank_value = 0
			if rank_value == ordinal_index + 1:
				return {key: value for key, value in item.items() if key in {"entity_type", "entity_key", "entity_label"}}
		if ordinal_index < len(candidates):
			item = candidates[ordinal_index]
			return {key: value for key, value in item.items() if key in {"entity_type", "entity_key", "entity_label"}}
	if not candidates:
		dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
		entity_type = clean_runtime_text(dimensions.get("entity_type"))
		entity_key = clean_runtime_text(
			dimensions.get("entity_key") or (artifact.get("filters") or {}).get("entity_key")
		)
		entity_label = clean_runtime_text(dimensions.get("entity_label") or entity_key)
		if entity_type and (entity_key or entity_label):
			candidates.append(
				{
					"entity_type": entity_type,
					"entity_key": entity_key or entity_label,
					"entity_label": entity_label or entity_key,
				}
			)
	unique_candidates: Dict[tuple[str, str, str], Dict[str, str]] = {}
	for item in candidates:
		key = (
			clean_runtime_text(item.get("entity_type")),
			clean_runtime_text(item.get("entity_key")),
			clean_runtime_text(item.get("entity_label")),
		)
		if key[0] and (key[1] or key[2]):
			unique_candidates[key] = item
	if len(unique_candidates) == 1:
		return next(iter(unique_candidates.values()))
	return {}


def recent_focus_contextual_reference(
	*,
	recent_focus_state: Dict[str, Any],
	grounded_turn: Dict[str, Any],
	artifact_payload: Dict[str, Any],
	raw_message: str = "",
) -> Dict[str, str]:
	if isinstance(recent_focus_state, dict) and bool(recent_focus_state.get("available")):
		focus_kind = clean_runtime_text(recent_focus_state.get("focus_kind"))
		if focus_kind in {"entity", "document"}:
			entity_type = clean_runtime_text(recent_focus_state.get("focus_grain"))
			entity_key = clean_runtime_text(recent_focus_state.get("focus_key"))
			entity_label = clean_runtime_text(recent_focus_state.get("focus_label")) or entity_key
			if entity_type and (entity_key or entity_label):
				return {
					"entity_type": entity_type,
					"entity_key": entity_key or entity_label,
					"entity_label": entity_label or entity_key,
				}
	return grounded_entity_reference(
		grounded_turn=grounded_turn,
		artifact_payload=artifact_payload,
		raw_message=raw_message,
	)


def compile_contextual_entity_breakout_message(
	*,
	raw_message: str,
	followup_resolution,
	recent_focus_state: Dict[str, Any],
	grounded_turn: Dict[str, Any],
	artifact_payload: Dict[str, Any],
	recent_focus_affordance_contract=None,
	continuation_contract=None,
) -> str:
	message = clean_runtime_text(raw_message)
	if not message:
		return ""
	followup_mode = str(getattr(followup_resolution, "mode", "") or "").strip()
	if followup_mode not in {"new_query", "grounded_follow_up", "local_grounded_transform"}:
		return ""
	if not bool(getattr(followup_resolution, "depends_on_grounded_turn", False)):
		return ""
	focus_kind = clean_runtime_text((recent_focus_state or {}).get("focus_kind"))
	listing_detail_context = (
		focus_kind == "listing"
		and bool(getattr(recent_focus_affordance_contract, "detail_supported", False))
	)
	if focus_kind not in {"entity", "document"} and not listing_detail_context:
		return ""
	entity_reference = recent_focus_contextual_reference(
		recent_focus_state=recent_focus_state,
		grounded_turn=grounded_turn,
		artifact_payload=artifact_payload,
		raw_message=message,
	)
	entity_type = clean_runtime_text(entity_reference.get("entity_type"))
	entity_key = clean_runtime_text(entity_reference.get("entity_key"))
	entity_label = clean_runtime_text(entity_reference.get("entity_label")) or entity_key
	entity_noun = _CONTEXTUAL_BREAKOUT_ENTITY_NOUNS.get(entity_type, "")
	if not entity_noun or not entity_label:
		return ""
	if (focus_kind == "document" or listing_detail_context) and looks_like_contextual_detail_request(message):
		return f"show me details for {entity_noun} {entity_label}".strip()
	normalized_message = normalize_runtime_text(message)
	if normalize_runtime_text(entity_label) in normalized_message or (
		entity_key and normalize_runtime_text(entity_key) in normalized_message
	):
		return ""
	if message.endswith("?"):
		base_message = message[:-1].rstrip()
		suffix = "?"
	else:
		base_message = message
		suffix = ""
	return f'{base_message} for {entity_noun} "{entity_label}"{suffix}'.strip()


def compile_recent_focus_runtime_message(
	*,
	request_id: str,
	raw_message: str,
	followup_resolution,
	recent_focus_state: Dict[str, Any],
	grounded_turn: Dict[str, Any],
	artifact_payload: Dict[str, Any],
	continuation_contract=None,
):
	recent_focus_affordance_contract = build_recent_focus_affordance_contract_from_snapshot(
		request_id=request_id,
		recent_focus_state=recent_focus_state,
	)
	if recent_focus_affordance_contract is None:
		return "", "", None
	routing_selection = recent_focus_runtime_route_selection(
		recent_focus_state=recent_focus_state,
		followup_resolution=followup_resolution,
		recent_focus_affordance_contract=recent_focus_affordance_contract,
	)
	if not bool(routing_selection.get("eligible")):
		return "", "", recent_focus_affordance_contract
	local_transform_allowed = bool(routing_selection.get("local_transform_allowed"))
	requery_allowed = bool(routing_selection.get("requery_allowed"))
	if local_transform_allowed:
		contextual_runtime_message = compile_contextual_entity_breakout_message(
			raw_message=raw_message,
			followup_resolution=followup_resolution,
			recent_focus_state=recent_focus_state,
			grounded_turn=grounded_turn,
			artifact_payload=artifact_payload,
			recent_focus_affordance_contract=recent_focus_affordance_contract,
			continuation_contract=continuation_contract,
		)
		if contextual_runtime_message:
			return contextual_runtime_message, "local_transform", recent_focus_affordance_contract
	if requery_allowed:
		return clean_runtime_text(raw_message), "shared_affordance", recent_focus_affordance_contract
	return "", "", recent_focus_affordance_contract
