from __future__ import annotations

import re
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.governed_scope_registry import canonical_scope_aliases_for_entity_grain
from ai_assistant_ui.qwen_chat.metadata import (
	entity_grain_display_label,
	get_entity_reference_policy_spec,
	load_semantic_resolution_registry,
)


def clean_lookup_text(value: Any) -> str:
	return str(value or "").strip()


def normalize_lookup_text(value: Any) -> str:
	return " ".join(clean_lookup_text(value).lower().split())


def message_contains_lookup_phrase(value: str, phrase: str) -> bool:
	text = normalize_lookup_text(value)
	target = normalize_lookup_text(phrase)
	if not text or not target:
		return False
	pattern = r"(^|[^a-z0-9])" + re.escape(target) + r"([^a-z0-9]|$)"
	if bool(re.search(pattern, text)):
		return True
	target_tokens = [token for token in re.split(r"[^a-z0-9]+", target) if token]
	if len(target_tokens) < 2:
		return False
	cursor = 0
	for token in target_tokens:
		match = re.search(r"(^|[^a-z0-9])" + re.escape(token) + r"([^a-z0-9]|$)", text[cursor:])
		if not match:
			return False
		cursor += match.end()
	return True


def slot_alias_entries(slot_name: str) -> List[Dict[str, Any]]:
	registry = load_semantic_resolution_registry()
	alias_maps = registry.get("alias_maps") if isinstance(registry.get("alias_maps"), dict) else {}
	return alias_maps.get(slot_name) if isinstance(alias_maps.get(slot_name), list) else []


def slot_alias_matches(slot_name: str, message: str) -> List[str]:
	entries = slot_alias_entries(slot_name)
	out: List[str] = []
	for entry in entries:
		if not isinstance(entry, dict):
			continue
		canonical_value = clean_lookup_text(entry.get("canonical_value"))
		if not canonical_value:
			continue
		aliases = [
			clean_lookup_text(alias)
			for alias in (entry.get("aliases") or [])
			if clean_lookup_text(alias)
		]
		if any(message_contains_lookup_phrase(message, alias) for alias in aliases):
			out.append(canonical_value)
	return list(dict.fromkeys(out))


def fallback_entity_grain_matches(message: str) -> List[str]:
	out: List[str] = []
	for entry in slot_alias_entries("entity_grain"):
		if not isinstance(entry, dict):
			continue
		canonical_value = clean_lookup_text(entry.get("canonical_value"))
		if not canonical_value:
			continue
		candidate_phrases = {
			canonical_value.replace("_", " "),
			clean_lookup_text(entity_grain_display_label(canonical_value, plural=False)),
			clean_lookup_text(entity_grain_display_label(canonical_value, plural=True)),
			*canonical_scope_aliases_for_entity_grain(canonical_value),
		}
		if any(message_contains_lookup_phrase(message, phrase) for phrase in candidate_phrases if clean_lookup_text(phrase)):
			out.append(canonical_value)
	return list(dict.fromkeys(out))


def first_non_empty(values: List[str]) -> str:
	for value in values:
		if clean_lookup_text(value):
			return clean_lookup_text(value)
	return ""


def slot_aliases_for_value(slot_name: str, canonical_value: str) -> List[str]:
	for entry in slot_alias_entries(slot_name):
		if not isinstance(entry, dict):
			continue
		if clean_lookup_text(entry.get("canonical_value")) != clean_lookup_text(canonical_value):
			continue
		return [
			clean_lookup_text(alias)
			for alias in (entry.get("aliases") or [])
			if clean_lookup_text(alias)
		]
	return []


def extract_suffix_after_alias(message: str, aliases: List[str]) -> str:
	text = clean_lookup_text(message)
	if not text:
		return ""
	best_start = -1
	best_length = -1
	for alias in aliases:
		pattern = re.compile(re.escape(alias), flags=re.IGNORECASE)
		match = pattern.search(text)
		if not match:
			continue
		if match.start() < best_start or best_start < 0:
			best_start = match.start()
			best_length = match.end() - match.start()
		elif match.start() == best_start and (match.end() - match.start()) > best_length:
			best_length = match.end() - match.start()
	if best_start < 0 or best_length <= 0:
		return ""
	return text[best_start + best_length :].strip(" :.-\n\t\"'")


def infer_entity_grains_from_message(message: str) -> List[str]:
	alias_matches = slot_alias_matches("entity_grain", message)
	if alias_matches:
		return alias_matches
	return fallback_entity_grain_matches(message)


def infer_lookup_mode_from_message(message: str) -> str:
	aliases = slot_alias_matches("lookup_mode", message)
	if aliases:
		return first_non_empty(aliases)
	entity_grains = infer_entity_grains_from_message(message)
	if entity_grains:
		normalized_message = normalize_lookup_text(message)
		scope_directory_aliases = [
			alias
			for grain in entity_grains
			for alias in canonical_scope_aliases_for_entity_grain(grain)
			if clean_lookup_text(alias) and any(token in normalize_lookup_text(alias) for token in ("directory", "master"))
		]
		if any(message_contains_lookup_phrase(normalized_message, alias) for alias in scope_directory_aliases):
			return "directory_list"
		similarity_cues = (
			"similar to",
			"similar",
			"closest",
			"match",
			"matches",
			"matching",
		)
		if any(message_contains_lookup_phrase(normalized_message, cue) for cue in similarity_cues):
			return ""
		directory_list_cues = (
			"show me",
			"give me",
			"list",
			"names",
			"name only",
			"full list",
		)
		if any(message_contains_lookup_phrase(normalized_message, cue) for cue in directory_list_cues):
			return "directory_list"
	return ""


def infer_lookup_projection_from_message(message: str, *, default_projection: str = "") -> str:
	aliases = slot_alias_matches("lookup_projection", message)
	if aliases:
		return first_non_empty(aliases)
	return clean_lookup_text(default_projection)


def extract_lookup_search_text(message: str, lookup_mode: str) -> str:
	text = clean_lookup_text(message)
	if not text:
		return ""
	match = re.search(r"[\"â€œ']([^\"â€']+)[\"â€']", str(message or ""))
	if match:
		return clean_lookup_text(match.group(1))
	aliases = slot_aliases_for_value("lookup_mode", lookup_mode)
	if aliases:
		return extract_suffix_after_alias(text, aliases)
	return ""


def infer_master_data_lookup_slots(
	*,
	message: str,
	entity_grain: str,
) -> Dict[str, Any]:
	policy = get_entity_reference_policy_spec(entity_grain)
	default_projection = clean_lookup_text(policy.get("default_projection"))
	default_limit = int(max(0, policy.get("default_limit") or 0)) if policy else 0
	lookup_mode = infer_lookup_mode_from_message(message)
	lookup_projection = infer_lookup_projection_from_message(
		message,
		default_projection=default_projection,
	)
	search_text = extract_lookup_search_text(message, lookup_mode)
	out: Dict[str, Any] = {}
	if lookup_mode:
		out["lookup_mode"] = lookup_mode
	if lookup_projection:
		out["lookup_projection"] = lookup_projection
	if search_text:
		out["lookup_search_text"] = search_text
	if default_limit > 0:
		out["lookup_limit"] = default_limit
	return out


def normalize_master_data_lookup_slots(
	*,
	message: str,
	entity_grain: str,
	preferred_slots: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	preferred = dict(preferred_slots or {}) if isinstance(preferred_slots, dict) else {}
	inferred = infer_master_data_lookup_slots(
		message=message,
		entity_grain=entity_grain,
	)
	out: Dict[str, Any] = {}
	for key in ("lookup_mode", "lookup_projection", "lookup_search_text"):
		preferred_value = clean_lookup_text(preferred.get(key))
		inferred_value = clean_lookup_text(inferred.get(key))
		if preferred_value:
			out[key] = preferred_value
		elif inferred_value:
			out[key] = inferred_value
	preferred_limit = preferred.get("lookup_limit")
	try:
		preferred_limit_int = int(max(0, preferred_limit or 0))
	except Exception:
		preferred_limit_int = 0
	inferred_limit = inferred.get("lookup_limit")
	try:
		inferred_limit_int = int(max(0, inferred_limit or 0))
	except Exception:
		inferred_limit_int = 0
	if preferred_limit_int > 0:
		out["lookup_limit"] = preferred_limit_int
	elif inferred_limit_int > 0:
		out["lookup_limit"] = inferred_limit_int
	return out
