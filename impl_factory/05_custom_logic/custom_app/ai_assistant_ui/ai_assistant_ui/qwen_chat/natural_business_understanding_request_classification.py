from __future__ import annotations

import re
from typing import Any

from .natural_business_understanding_context_resolution import nbu_ordinal_reference_index


VISIBLE_CONTEXT_TERMS = {
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

DEICTIC_ENTITY_TERMS = {"that", "this", "it", "same", "selected"}
TEMPORAL_CONTEXT_TERMS = {"last", "current", "this"}
FRESH_QUERY_VERBS = {"show", "list", "give", "get", "display", "find"}
FRESH_RANKING_TERMS = {"top", "bottom", "ranking", "rankings", "ranked"}
BUSINESS_OBJECT_TERMS = {
	"customer",
	"customers",
	"supplier",
	"suppliers",
	"product",
	"products",
	"item",
	"items",
	"invoice",
	"invoices",
	"receipt",
	"receipts",
	"payment",
	"payments",
	"statement",
	"statements",
	"stock",
	"stocks",
	"warehouse",
	"warehouses",
	"ar",
	"ap",
	"receivable",
	"receivables",
	"payable",
	"payables",
}
BUSINESS_METRIC_TERMS = {
	"revenue",
	"sales",
	"amount",
	"quantity",
	"qty",
	"profit",
	"margin",
	"outstanding",
	"overdue",
	"risk",
	"risky",
	"stock",
	"balance",
	"value",
}
EXPLICIT_CONTEXT_ANCHORS = {"above", "table", "row", "position", "that", "this", "it", "same", "selected"}
PRESENTATION_VERBS = {"show", "display", "format", "present", "convert", "as", "in"}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def normalize_message_text(value: Any) -> str:
	text = re.sub(r"[^a-z0-9]+", " ", _clean_text(value).lower())
	return " ".join(text.split()).strip()


def message_tokens(value: Any) -> set[str]:
	return {token for token in normalize_message_text(value).split() if token}


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
	tokens = message_tokens(message)
	if not tokens:
		return False
	if tokens.intersection({"million", "millions"}) and tokens.intersection(PRESENTATION_VERBS):
		return True
	if (
		tokens.intersection({"table", "markdown", "bullet", "bullets"})
		and tokens.intersection(FRESH_QUERY_VERBS.union({"format", "present"}))
		and not tokens.intersection(BUSINESS_OBJECT_TERMS)
	):
		return True
	return False


def fresh_business_query_requested(message: str) -> bool:
	tokens = message_tokens(message)
	if not tokens:
		return False
	business_terms = BUSINESS_OBJECT_TERMS.union(BUSINESS_METRIC_TERMS)
	if tokens.intersection({"top", "bottom"}) and tokens.intersection(business_terms):
		return True
	if tokens.intersection(FRESH_RANKING_TERMS) and tokens.intersection(BUSINESS_OBJECT_TERMS) and tokens.intersection(BUSINESS_METRIC_TERMS):
		return True
	if (
		tokens.intersection(FRESH_QUERY_VERBS)
		and tokens.intersection(BUSINESS_OBJECT_TERMS)
		and not tokens.intersection(EXPLICIT_CONTEXT_ANCHORS)
	):
		return True
	return False


def _context_tokens(message: str) -> set[str]:
	tokens = set(message_tokens(message))
	if temporal_scope_phrase_present(message):
		tokens.difference_update(TEMPORAL_CONTEXT_TERMS)
	return tokens


def visible_context_reference_requested(message: str) -> bool:
	if presentation_only_transform_requested(message):
		return False
	if fresh_business_query_requested(message):
		return False
	if nbu_ordinal_reference_index(message) >= 0:
		return True
	return bool(_context_tokens(message).intersection(VISIBLE_CONTEXT_TERMS))


def visible_context_target_reference(message: str) -> str:
	if nbu_ordinal_reference_index(message) >= 0:
		return "rank_n"
	if _context_tokens(message).intersection(DEICTIC_ENTITY_TERMS):
		return "selected_entity"
	return "current_artifact"
