from __future__ import annotations

from difflib import SequenceMatcher
import re
from typing import Any, Dict, List

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	class _FallbackDB:
		def exists(self, *args, **kwargs):
			return False

		def get_value(self, *args, **kwargs):
			return None

	class _FallbackFrappe:
		db = _FallbackDB()

		def get_all(self, *args, **kwargs):
			return []

	frappe = _FallbackFrappe()  # type: ignore

from ai_assistant_ui.qwen_chat.contracts import build_entity_reference_resolution_contract
from ai_assistant_ui.qwen_chat.governed_scope_registry import (
	canonical_scope_aliases_for_entity_grain,
)
from ai_assistant_ui.qwen_chat.metadata import (
	entity_grain_display_label,
	get_entity_reference_policy_spec,
	load_semantic_resolution_registry,
)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _normalize_text(value: Any) -> str:
	return " ".join(_clean_text(value).lower().split())


def _message_contains_phrase(value: str, phrase: str) -> bool:
	text = _normalize_text(value)
	target = _normalize_text(phrase)
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


def _slot_alias_entries(slot_name: str) -> List[Dict[str, Any]]:
	registry = load_semantic_resolution_registry()
	alias_maps = registry.get("alias_maps") if isinstance(registry.get("alias_maps"), dict) else {}
	return alias_maps.get(slot_name) if isinstance(alias_maps.get(slot_name), list) else []


def _slot_alias_matches(slot_name: str, message: str) -> List[str]:
	entries = _slot_alias_entries(slot_name)
	out: List[str] = []
	for entry in entries:
		if not isinstance(entry, dict):
			continue
		canonical_value = _clean_text(entry.get("canonical_value"))
		if not canonical_value:
			continue
		aliases = [
			_clean_text(alias)
			for alias in (entry.get("aliases") or [])
			if _clean_text(alias)
		]
		if any(_message_contains_phrase(message, alias) for alias in aliases):
			out.append(canonical_value)
	return list(dict.fromkeys(out))


def _fallback_entity_grain_matches(message: str) -> List[str]:
	out: List[str] = []
	for entry in _slot_alias_entries("entity_grain"):
		if not isinstance(entry, dict):
			continue
		canonical_value = _clean_text(entry.get("canonical_value"))
		if not canonical_value:
			continue
		candidate_phrases = {
			canonical_value.replace("_", " "),
			_clean_text(entity_grain_display_label(canonical_value, plural=False)),
			_clean_text(entity_grain_display_label(canonical_value, plural=True)),
			*canonical_scope_aliases_for_entity_grain(canonical_value),
		}
		if any(_message_contains_phrase(message, phrase) for phrase in candidate_phrases if _clean_text(phrase)):
			out.append(canonical_value)
	return list(dict.fromkeys(out))


def _first_non_empty(values: List[str]) -> str:
	for value in values:
		if _clean_text(value):
			return _clean_text(value)
	return ""


def _slot_aliases_for_value(slot_name: str, canonical_value: str) -> List[str]:
	for entry in _slot_alias_entries(slot_name):
		if not isinstance(entry, dict):
			continue
		if _clean_text(entry.get("canonical_value")) != _clean_text(canonical_value):
			continue
		return [
			_clean_text(alias)
			for alias in (entry.get("aliases") or [])
			if _clean_text(alias)
		]
	return []


def _extract_suffix_after_alias(message: str, aliases: List[str]) -> str:
	text = _clean_text(message)
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
	return text[best_start + best_length:].strip(" :.-\n\t\"'")


def infer_lookup_mode_from_message(message: str) -> str:
	aliases = _slot_alias_matches("lookup_mode", message)
	if aliases:
		return _first_non_empty(aliases)
	entity_grains = infer_entity_grains_from_message(message)
	if entity_grains:
		normalized_message = _normalize_text(message)
		scope_directory_aliases = [
			alias
			for grain in entity_grains
			for alias in canonical_scope_aliases_for_entity_grain(grain)
			if _clean_text(alias) and any(token in _normalize_text(alias) for token in ("directory", "master"))
		]
		if any(_message_contains_phrase(normalized_message, alias) for alias in scope_directory_aliases):
			return "directory_list"
		similarity_cues = (
			"similar to",
			"similar",
			"closest",
			"match",
			"matches",
			"matching",
		)
		if any(_message_contains_phrase(normalized_message, cue) for cue in similarity_cues):
			return ""
		directory_list_cues = (
			"show me",
			"give me",
			"list",
			"names",
			"name only",
			"full list",
		)
		if any(_message_contains_phrase(normalized_message, cue) for cue in directory_list_cues):
			return "directory_list"
	return ""


def infer_lookup_projection_from_message(message: str, *, default_projection: str = "") -> str:
	aliases = _slot_alias_matches("lookup_projection", message)
	if aliases:
		return _first_non_empty(aliases)
	return _clean_text(default_projection)


def infer_entity_grains_from_message(message: str) -> List[str]:
	alias_matches = _slot_alias_matches("entity_grain", message)
	if alias_matches:
		return alias_matches
	return _fallback_entity_grain_matches(message)


def _extract_search_text_from_quotes(message: str) -> str:
	match = re.search(r"[\"“']([^\"”']+)[\"”']", str(message or ""))
	if match:
		return _clean_text(match.group(1))
	return ""


def extract_lookup_search_text(message: str, lookup_mode: str) -> str:
	text = _clean_text(message)
	if not text:
		return ""
	quoted = _extract_search_text_from_quotes(text)
	if quoted:
		return quoted
	aliases = _slot_aliases_for_value("lookup_mode", lookup_mode)
	if aliases:
		return _extract_suffix_after_alias(text, aliases)
	return ""


def infer_master_data_lookup_slots(
	*,
	message: str,
	entity_grain: str,
) -> Dict[str, Any]:
	policy = get_entity_reference_policy_spec(entity_grain)
	default_projection = _clean_text(policy.get("default_projection"))
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
		preferred_value = _clean_text(preferred.get(key))
		inferred_value = _clean_text(inferred.get(key))
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


def _text_tokens(value: Any) -> List[str]:
	text = re.sub(r"[^a-z0-9]+", " ", _normalize_text(value))
	return [token for token in text.split() if token]


def _candidate_match(
	*,
	search_text: str,
	candidate_label: str,
) -> Dict[str, Any]:
	def _ordered_token_coverage(search_tokens: List[str], label_tokens: List[str]) -> bool:
		if not search_tokens or not label_tokens:
			return False
		cursor = 0
		for token in search_tokens:
			found = False
			while cursor < len(label_tokens):
				if label_tokens[cursor] == token:
					found = True
					cursor += 1
					break
				cursor += 1
			if not found:
				return False
		return True

	if _message_contains_phrase(candidate_label, search_text) or _message_contains_phrase(search_text, candidate_label):
		return {
			"match_mode": "exact_phrase",
			"confidence": 1.0,
			"overlap_count": len(_text_tokens(candidate_label)),
		}
	search_tokens = _text_tokens(search_text)
	label_tokens = _text_tokens(candidate_label)
	if len(label_tokens) < 2 or len(search_tokens) < 2:
		return {}
	search_token_set = set(search_tokens)
	overlap_count = len(search_token_set.intersection(label_tokens))
	search_coverage = float(overlap_count) / float(len(search_token_set) or 1)
	label_coverage = float(overlap_count) / float(len(label_tokens) or 1)
	if (
		len(search_token_set) >= 3
		and search_coverage >= 0.8
		and _ordered_token_coverage(search_tokens, label_tokens)
	):
		return {
			"match_mode": "ordered_token_cover",
			"confidence": round(min(0.96, 0.84 + (search_coverage * 0.12)), 4),
			"overlap_count": overlap_count,
		}
	min_overlap = 2 if len(label_tokens) <= 3 else max(3, len(label_tokens) - 1)
	if overlap_count >= min_overlap and label_coverage >= 0.8:
		return {
			"match_mode": "token_overlap",
			"confidence": label_coverage,
			"overlap_count": overlap_count,
		}
	string_similarity = SequenceMatcher(
		None,
		" ".join(search_tokens),
		" ".join(label_tokens),
	).ratio()
	if overlap_count >= 2 and string_similarity >= 0.82:
		return {
			"match_mode": "string_similarity",
			"confidence": round(string_similarity, 4),
			"overlap_count": overlap_count,
		}
	return {}


def _dedupe_candidate_entities(candidate_entities: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
	by_visible_label: Dict[str, Dict[str, Any]] = {}
	for item in candidate_entities or []:
		if not isinstance(item, dict):
			continue
		entity_label = _clean_text(item.get("entity_label") or item.get("entity_key"))
		normalized_label = _normalize_text(entity_label)
		if not normalized_label:
			continue
		existing = by_visible_label.get(normalized_label)
		current_confidence = float(item.get("confidence") or 0.0)
		existing_confidence = float(existing.get("confidence") or 0.0) if isinstance(existing, dict) else -1.0
		if existing is None or current_confidence > existing_confidence:
			by_visible_label[normalized_label] = dict(item)
	return sorted(
		by_visible_label.values(),
		key=lambda item: (
			float(item.get("confidence") or 0.0),
			_clean_text(item.get("entity_label") or item.get("entity_key")),
		),
		reverse=True,
	)


def resolve_entity_reference_from_message(
	*,
	request_id: str,
	entity_grain: str,
	message: str,
	lookup_mode: str = "",
	search_text: str = "",
) -> Dict[str, Any]:
	grain = _clean_text(entity_grain)
	normalized_slots = normalize_master_data_lookup_slots(
		message=message,
		entity_grain=grain,
		preferred_slots={
			"lookup_mode": lookup_mode,
			"lookup_search_text": search_text,
		},
	)
	resolved_lookup_mode = _clean_text(normalized_slots.get("lookup_mode"))
	resolved_search_text = _clean_text(normalized_slots.get("lookup_search_text"))
	policy = get_entity_reference_policy_spec(grain)
	if not policy or _clean_text(policy.get("activation_state")) != "active":
		return build_entity_reference_resolution_contract(
			request_id=request_id,
			entity_grain=grain,
			lookup_mode=resolved_lookup_mode,
			search_text=resolved_search_text,
			resolution_status="unsupported_grain",
			reason="No active governed entity reference policy exists for this grain.",
		).to_payload()
	doctype = _clean_text(policy.get("doctype"))
	identity_field = _clean_text(policy.get("identity_field"))
	display_field = _clean_text(policy.get("display_field"))
	search_fields = [
		_clean_text(value)
		for value in (policy.get("search_fields") or [])
		if _clean_text(value)
	]
	match_policy = _clean_text(policy.get("match_policy"))
	if resolved_lookup_mode and resolved_lookup_mode not in [str(v or "").strip() for v in (policy.get("allowed_lookup_modes") or [])]:
		return build_entity_reference_resolution_contract(
			request_id=request_id,
			entity_grain=grain,
			lookup_mode=resolved_lookup_mode,
			search_text=resolved_search_text,
			resolution_status="unsupported_mode",
			reason="The requested lookup mode is not active for this governed entity grain.",
		).to_payload()
	if not resolved_search_text:
		return build_entity_reference_resolution_contract(
			request_id=request_id,
			entity_grain=grain,
			lookup_mode=resolved_lookup_mode,
			search_text="",
			resolution_status="not_found",
			reason="No concrete governed entity reference could be extracted from the current request.",
		).to_payload()
	if doctype and identity_field and frappe.db.exists(doctype, resolved_search_text):
		display_value = _clean_text(frappe.db.get_value(doctype, resolved_search_text, display_field)) if display_field else ""
		return build_entity_reference_resolution_contract(
			request_id=request_id,
			entity_grain=grain,
			lookup_mode=resolved_lookup_mode,
			search_text=resolved_search_text,
			resolution_status="resolved",
			resolved_entity={
				"entity_type": grain,
				"entity_key": resolved_search_text,
				"entity_label": display_value or resolved_search_text,
				"resolution_source": "exact_name",
			},
			reason="The request matched a governed entity key exactly.",
		).to_payload()
	if doctype and display_field:
		row = frappe.db.get_value(doctype, {display_field: resolved_search_text}, [identity_field, display_field], as_dict=True)
		if isinstance(row, dict) and _clean_text(row.get(identity_field)):
			entity_key = _clean_text(row.get(identity_field))
			entity_label = _clean_text(row.get(display_field)) or entity_key
			return build_entity_reference_resolution_contract(
				request_id=request_id,
				entity_grain=grain,
				lookup_mode=resolved_lookup_mode,
				search_text=resolved_search_text,
				resolution_status="resolved",
				resolved_entity={
					"entity_type": grain,
					"entity_key": entity_key,
					"entity_label": entity_label,
					"resolution_source": "exact_display",
				},
				reason="The request matched a governed entity display label exactly.",
			).to_payload()
	if match_policy != "exact_then_governed_fuzzy" or not doctype or not search_fields:
		return build_entity_reference_resolution_contract(
			request_id=request_id,
			entity_grain=grain,
			lookup_mode=resolved_lookup_mode,
			search_text=resolved_search_text,
			resolution_status="not_found",
			reason="No governed entity matched the requested reference.",
		).to_payload()
	rows = frappe.get_all(
		doctype,
		fields=list(dict.fromkeys([identity_field, display_field] + search_fields)),
		limit_page_length=5000,
		order_by="modified desc",
	)
	best_row: Dict[str, Any] = {}
	best_confidence = 0.0
	second_confidence = 0.0
	best_overlap = 0
	candidate_map: Dict[str, Dict[str, Any]] = {}
	for row in rows or []:
		if not isinstance(row, dict):
			continue
		entity_key = _clean_text(row.get(identity_field))
		entity_label = _clean_text(row.get(display_field)) or entity_key
		if not entity_key:
			continue
		label_candidates = [
			entity_label,
			entity_key,
		]
		for field_name in search_fields:
			label_candidates.append(_clean_text(row.get(field_name)))
		for candidate_label in [value for value in label_candidates if value]:
			match = _candidate_match(search_text=resolved_search_text, candidate_label=candidate_label)
			if not match:
				continue
			confidence = float(match.get("confidence") or 0.0)
			overlap_count = int(match.get("overlap_count") or 0)
			existing_candidate = candidate_map.get(entity_key) if entity_key else None
			if not existing_candidate or confidence > float(existing_candidate.get("confidence") or 0.0):
				candidate_map[entity_key] = {
					"entity_type": grain,
					"entity_key": entity_key,
					"entity_label": entity_label,
					"resolution_source": str(match.get("match_mode") or "").strip() or "governed_fuzzy",
					"confidence": round(confidence, 4),
				}
			if confidence > best_confidence or (confidence == best_confidence and overlap_count > best_overlap):
				second_confidence = best_confidence
				best_row = dict(row)
				best_confidence = confidence
				best_overlap = overlap_count
			elif confidence > second_confidence:
				second_confidence = confidence
	candidate_entities = sorted(
		candidate_map.values(),
		key=lambda item: (
			float(item.get("confidence") or 0.0),
			_clean_text(item.get("entity_label")),
		),
		reverse=True,
	)
	candidate_entities = _dedupe_candidate_entities(candidate_entities)
	if best_row and best_confidence >= 0.8:
		entity_key = _clean_text(best_row.get(identity_field))
		entity_label = _clean_text(best_row.get(display_field)) or entity_key
		if (best_confidence - second_confidence) < 0.05 and len(candidate_entities) > 1:
			return build_entity_reference_resolution_contract(
				request_id=request_id,
				entity_grain=grain,
				lookup_mode=resolved_lookup_mode,
				search_text=resolved_search_text,
				resolution_status="ambiguous",
				candidate_entities=candidate_entities[:5],
				reason="Multiple governed entities matched the requested reference too closely to resolve safely.",
			).to_payload()
		return build_entity_reference_resolution_contract(
			request_id=request_id,
			entity_grain=grain,
			lookup_mode=resolved_lookup_mode,
			search_text=resolved_search_text,
			resolution_status="resolved",
			candidate_entities=candidate_entities[:5],
			resolved_entity={
				"entity_type": grain,
				"entity_key": entity_key,
				"entity_label": entity_label,
				"resolution_source": "governed_fuzzy",
			},
			reason="The request matched one governed entity confidently through approved fuzzy resolution.",
		).to_payload()
	if candidate_entities:
		return build_entity_reference_resolution_contract(
			request_id=request_id,
			entity_grain=grain,
			lookup_mode=resolved_lookup_mode,
			search_text=resolved_search_text,
			resolution_status="not_found",
			candidate_entities=candidate_entities[:5],
			reason="No governed entity matched the requested reference confidently enough.",
		).to_payload()
	return build_entity_reference_resolution_contract(
		request_id=request_id,
		entity_grain=grain,
		lookup_mode=resolved_lookup_mode,
		search_text=resolved_search_text,
		resolution_status="not_found",
		reason="No governed entity matched the requested reference confidently enough.",
	).to_payload()
