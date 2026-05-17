from __future__ import annotations

import re
from typing import Any

from .metadata import ontology_detect_concepts, ontology_detect_followup_modes
from .natural_business_understanding_context_resolution import nbu_ordinal_reference_index
from .semantic_aliases import detect_canonical_keys


DISCOURSE_CONTEXT_MARKERS = {
	"above",
	"current",
	"latest",
	"last",
	"rank",
	"row",
	"position",
	"table",
	"that",
	"this",
	"it",
	"same",
	"selected",
}
ARTIFACT_SET_CONTEXT_MARKERS = {
	"above",
	"current",
	"latest",
	"last",
	"shown",
	"table",
}
DEICTIC_ENTITY_MARKERS = {
	"that",
	"this",
	"it",
	"same",
	"selected",
}
TEMPORAL_CONTEXT_TERMS = {"last", "current", "this"}
ARTIFACT_CONTEXT_FOLLOWUP_MODES = {
	"aging_bucket_view",
	"bullet_presentation",
	"column_projection",
	"dimension_breakdown",
	"metric_refinement",
	"presentation_transform",
	"sort_or_limit",
	"table_presentation",
	"time_scope_restatement",
}
PRESENTATION_ONLY_FOLLOWUP_MODES = {
	"bullet_presentation",
	"column_projection",
	"presentation_transform",
	"table_presentation",
}
ENTITY_REFERENCE_DIMENSIONS = {
	"account",
	"customer",
	"document",
	"invoice",
	"item",
	"item_code",
	"item_name",
	"party",
	"supplier",
	"warehouse",
}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def normalize_message_text(value: Any) -> str:
	text = re.sub(r"[^a-z0-9]+", " ", _clean_text(value).lower())
	return " ".join(text.split()).strip()


def message_tokens(value: Any) -> set[str]:
	return {token for token in normalize_message_text(value).split() if token}


def _contains_any_token(tokens: set[str], values: set[str]) -> bool:
	return any(value in tokens for value in values)


def _metadata_business_signal(message: str) -> bool:
	try:
		if ontology_detect_concepts(message, include_extended=False):
			return True
	except Exception:
		pass
	for dimension_or_metric in ("metric", "dimension"):
		try:
			if detect_canonical_keys(text=message, dimension_or_metric=dimension_or_metric):
				return True
		except Exception:
			continue
	return False


def _entity_reference_signal(message: str) -> bool:
	try:
		dimensions = detect_canonical_keys(text=message, dimension_or_metric="dimension")
	except Exception:
		dimensions = []
	return any(str(value or "").strip() in ENTITY_REFERENCE_DIMENSIONS for value in dimensions)


def _followup_modes(message: str) -> set[str]:
	try:
		return {
			str(value or "").strip()
			for value in ontology_detect_followup_modes(message)
			if str(value or "").strip()
		}
	except Exception:
		return set()


def temporal_scope_phrase_present(message: str) -> bool:
	normalized = normalize_message_text(message)
	if not normalized:
		return False
	return bool(
		re.search(
			r"\b(?:last|this|current|next|previous|prior)\s+"
			r"(?:month|months|week|weeks|year|years|quarter|quarters|day|days|period|fiscal|fy)\b",
			normalized,
		)
		or re.search(r"\b(?:fiscal\s+year|current\s+fiscal\s+year|last\s+fiscal\s+year|ytd|mtd|qtd)\b", normalized)
	)


def presentation_only_transform_requested(message: str) -> bool:
	if nbu_ordinal_reference_index(message) != -1:
		return False
	modes = _followup_modes(message)
	return any(mode in PRESENTATION_ONLY_FOLLOWUP_MODES for mode in modes)


def fresh_business_query_requested(message: str) -> bool:
	if not _metadata_business_signal(message):
		return False
	return not _contains_any_token(message_tokens(message), DISCOURSE_CONTEXT_MARKERS)


def _context_tokens(message: str) -> set[str]:
	normalized = normalize_message_text(message)
	if not normalized:
		return set()
	context_surface = re.sub(
		r"\b(?:last|this|current|next|previous|prior)\s+"
		r"(?:month|months|week|weeks|year|years|quarter|quarters|day|days|period|fiscal|fy)\b",
		" ",
		normalized,
	)
	context_surface = re.sub(
		r"\b(?:fiscal\s+year|current\s+fiscal\s+year|last\s+fiscal\s+year|ytd|mtd|qtd)\b",
		" ",
		context_surface,
	)
	return message_tokens(context_surface)


def _artifact_set_reference_signal(message: str) -> bool:
	tokens = _context_tokens(message)
	if not tokens:
		return False
	if _contains_any_token(tokens, DEICTIC_ENTITY_MARKERS):
		return False
	return bool(_contains_any_token(tokens, ARTIFACT_SET_CONTEXT_MARKERS) and _entity_reference_signal(message))


def visible_context_reference_requested(message: str) -> bool:
	if presentation_only_transform_requested(message):
		return False
	if nbu_ordinal_reference_index(message) != -1:
		return True
	if fresh_business_query_requested(message):
		return False
	return _contains_any_token(_context_tokens(message), DISCOURSE_CONTEXT_MARKERS)


def artifact_level_visible_context_requested(message: str) -> bool:
	tokens = _context_tokens(message)
	if not tokens:
		return False
	if nbu_ordinal_reference_index(message) != -1:
		return False
	if _artifact_set_reference_signal(message):
		return True
	if _entity_reference_signal(message):
		return False
	modes = _followup_modes(message)
	return any(mode in ARTIFACT_CONTEXT_FOLLOWUP_MODES for mode in modes) or _contains_any_token(
		tokens,
		DISCOURSE_CONTEXT_MARKERS,
	)


def visible_context_target_reference(message: str) -> str:
	if nbu_ordinal_reference_index(message) != -1:
		return "rank_n"
	if _artifact_set_reference_signal(message):
		return "current_artifact"
	if artifact_level_visible_context_requested(message):
		return "current_artifact"
	if _contains_any_token(_context_tokens(message), DISCOURSE_CONTEXT_MARKERS):
		return "selected_entity"
	return "current_artifact"
