from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List

from ai_assistant_ui.qwen_chat.metadata import (
	capability_dimensions_for_report,
	governed_self_contained_business_terms,
	load_business_ontology,
	ontology_self_contained_prefixes,
	report_local_followup_adapter,
)


def _normalize_text(text: str) -> str:
	return " ".join(str(text or "").strip().lower().split())


def _contains_alias(text: str, alias: str) -> bool:
	value = _normalize_text(text)
	target = _normalize_text(alias)
	if not value or not target:
		return False
	pattern = r"(^|[^a-z0-9])" + re.escape(target) + r"([^a-z0-9]|$)"
	return bool(re.search(pattern, value))


@dataclass(frozen=True)
class FollowUpIntent:
	requested_modes: List[str]
	matched_aliases: Dict[str, List[str]]
	target_dimension: str = ""
	target_limit: int = 0
	sort_direction: str = ""


def _normalized_dimension_candidates(grounded_turn: Dict[str, object] | None) -> Dict[str, str]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	report_name = str(turn.get("source_name") or "").strip()
	candidates: Dict[str, str] = {}

	adapter = report_local_followup_adapter(report_name, "dimension_breakdown")
	display_dimension = str(adapter.get("display_dimension_label") or "").strip()
	if display_dimension:
		candidates[_normalize_text(display_dimension)] = display_dimension

	for value in capability_dimensions_for_report(report_name):
		clean = str(value or "").strip()
		if clean:
			candidates.setdefault(_normalize_text(clean), clean)

	for value in turn.get("dimensions") or []:
		clean = str(value or "").strip()
		if clean:
			candidates.setdefault(_normalize_text(clean), clean)

	returned_schema = turn.get("returned_schema")
	if isinstance(returned_schema, list):
		for value in returned_schema[:2]:
			clean = str(value or "").strip()
			if clean:
				candidates.setdefault(_normalize_text(clean), clean)

	return candidates


def _detect_dimension_breakdown_target(text: str, grounded_turn: Dict[str, object] | None) -> str:
	match = re.search(r"\b(?:show|group|breakdown|split)\s+by\s+([a-z0-9 _-]+)$", text)
	if not match:
		return ""
	target = _normalize_text(match.group(1))
	if not target:
		return ""
	candidates = _normalized_dimension_candidates(grounded_turn)
	return str(candidates.get(target) or "")


def _detect_sort_limit_spec(text: str) -> tuple[int, str]:
	limit = 0
	direction = ""

	top_match = re.search(r"\btop\s+(\d+)\b", text)
	if top_match:
		limit = int(top_match.group(1))
		direction = "desc"

	bottom_match = re.search(r"\b(?:bottom|lowest)\s+(\d+)\b", text)
	if bottom_match:
		limit = int(bottom_match.group(1))
		direction = "asc"

	if re.search(r"\b(?:highest|largest|biggest|descending|desc)\b", text):
		direction = "desc"
	if re.search(r"\b(?:lowest|smallest|ascending|asc)\b", text):
		direction = "asc"

	return max(0, int(limit)), direction


def detect_followup_intent(message: str, language: str = "en", grounded_turn: Dict[str, object] | None = None) -> FollowUpIntent:
	text = _normalize_text(message)
	if not text:
		return FollowUpIntent(requested_modes=[], matched_aliases={}, target_dimension="", target_limit=0, sort_direction="")
	entries = load_business_ontology().get("follow_up_classes")
	if not isinstance(entries, list):
		return FollowUpIntent(requested_modes=[], matched_aliases={}, target_dimension="", target_limit=0, sort_direction="")

	requested_modes: List[str] = []
	matched_aliases: Dict[str, List[str]] = {}
	for item in entries:
		if not isinstance(item, dict):
			continue
		mode = str(item.get("mode") or "").strip()
		aliases = item.get("aliases")
		if not mode or not isinstance(aliases, dict):
			continue
		values = aliases.get(language)
		if not isinstance(values, list):
			continue
		matches = [
			str(alias or "").strip()
			for alias in values
			if str(alias or "").strip() and _contains_alias(text, str(alias or ""))
		]
		if matches:
			requested_modes.append(mode)
			matched_aliases[mode] = matches

	if "million" in text.split() and "presentation_transform" not in requested_modes:
		requested_modes.append("presentation_transform")
		matched_aliases.setdefault("presentation_transform", []).append("million")

	target_dimension = _detect_dimension_breakdown_target(text, grounded_turn)
	if target_dimension:
		requested_modes.append("dimension_breakdown")
		matched_aliases.setdefault("dimension_breakdown", []).append(target_dimension)

	target_limit, sort_direction = _detect_sort_limit_spec(text)
	if target_limit or sort_direction:
		requested_modes.append("sort_or_limit")
		sort_matches: List[str] = []
		if target_limit:
			sort_matches.append(f"top {target_limit}" if sort_direction != "asc" else f"bottom {target_limit}")
		if sort_direction and not target_limit:
			sort_matches.append(sort_direction)
		matched_aliases.setdefault("sort_or_limit", []).extend(sort_matches or ["sort"])

	return FollowUpIntent(
		requested_modes=list(dict.fromkeys(requested_modes)),
		matched_aliases=matched_aliases,
		target_dimension=target_dimension,
		target_limit=target_limit,
		sort_direction=sort_direction,
	)


def is_million_transform_intent(message: str, intent: FollowUpIntent | None = None) -> bool:
	parsed = intent or detect_followup_intent(message)
	return "presentation_transform" in parsed.requested_modes


def is_self_contained_business_request(
	message: str,
	language: str = "en",
	intent: FollowUpIntent | None = None,
	grounded_turn: Dict[str, object] | None = None,
) -> bool:
	text = _normalize_text(message)
	terms = governed_self_contained_business_terms(language)
	if len(text.split()) < 3:
		return False
	if len(text.split()) < 4 and not any(_contains_alias(text, token) for token in terms):
		return False
	parsed = intent or detect_followup_intent(text, language=language, grounded_turn=grounded_turn)
	has_grounded_turn = bool(isinstance(grounded_turn, dict) and grounded_turn.get("grounded"))
	if has_grounded_turn and {"presentation_transform", "dimension_breakdown", "sort_or_limit"}.intersection(parsed.requested_modes):
		return False
	prefixes = ontology_self_contained_prefixes(language)
	if not any(text.startswith(f"{prefix} ") or text == prefix for prefix in prefixes):
		return False
	return any(_contains_alias(text, token) for token in terms)


def is_safe_local_compatibility_intent(
	message: str,
	language: str = "en",
	grounded_turn: Dict[str, object] | None = None,
) -> bool:
	parsed = detect_followup_intent(message, language=language, grounded_turn=grounded_turn)
	modes = set(parsed.requested_modes)
	if not modes:
		return False
	if not modes.issubset({"presentation_transform", "table_presentation", "sort_or_limit"}):
		return False
	if "sort_or_limit" in modes and not (parsed.target_limit or parsed.sort_direction):
		return False
	return True
