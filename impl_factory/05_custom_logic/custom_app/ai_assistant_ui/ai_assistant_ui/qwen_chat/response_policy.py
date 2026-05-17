from __future__ import annotations

import re
from typing import Any, Dict


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _message_tokens(value: str) -> set[str]:
	text = re.sub(r"[^a-z0-9]+", " ", _clean_text(value).lower())
	return {token for token in text.split() if token}


def _is_statement_question(text: str, tokens: set[str]) -> bool:
	if {"balance", "sheet"}.issubset(tokens):
		return True
	if {"cash", "flow"}.issubset(tokens):
		return True
	if {"income", "statement"}.issubset(tokens):
		return True
	if {"profit", "loss"}.issubset(tokens):
		return True
	return bool(re.search(r"\bp\s*&?\s*l\b", text.lower()))


def _is_operational_list_question(tokens: set[str]) -> bool:
	document_terms = {"invoice", "invoices", "payment", "payments", "transaction", "transactions", "ledger", "entries"}
	list_terms = {"last", "latest", "recent", "list", "show"}
	return bool(tokens & document_terms) and bool(tokens & list_terms)


def _is_ranking_or_trend_question(tokens: set[str]) -> bool:
	ranking_terms = {"top", "bottom", "rank", "ranking", "highest", "lowest", "best", "worst", "trend", "trends", "monthly", "weekly", "daily"}
	return bool(tokens & ranking_terms)


def _detect_preferred_formats(text: str, tokens: set[str]) -> list[str]:
	preferred: list[str] = []
	lower = text.lower()
	if any(phrase in lower for phrase in ("with table", "as table", "in table", "show table", "tabular")) or "table" in tokens:
		preferred.append("table")
	if any(
		phrase in lower
		for phrase in (
			"bullet point",
			"bullet points",
			"with bullet",
			"as bullets",
			"as bullet points",
			"key points",
			"facts as bullet",
			"bullet list",
		)
	):
		preferred.append("bullet_points")
	if any(token in tokens for token in {"detail", "details", "breakdown", "list", "numbers", "clearly"}):
		if "table" not in preferred:
			preferred.append("table")
		if "bullet_points" not in preferred:
			preferred.append("bullet_points")
	return preferred


def derive_response_policy(
	*,
	raw_message: str,
	analysis_requested: bool,
	followup_mode: str = "",
	self_contained: bool = True,
) -> Dict[str, Any]:
	# Presentation-only policy: these heuristics may shape answer format and narrative
	# structure, but they must not be treated as family/capability/report routing authority.
	text = _clean_text(raw_message)
	tokens = _message_tokens(text)
	followup_mode_key = _clean_text(followup_mode) or "new_query"
	is_followup = followup_mode_key != "new_query" or not bool(self_contained)
	preferred_formats = _detect_preferred_formats(text, tokens)

	answer_style = "simple_factual"
	policy_mode = "factual_default"
	highlight_allowed = True
	implication_allowed = False
	recommendation_allowed = False
	supporting_table_preference = "when_helpful"
	followup_conversational = is_followup
	structure = ["direct_answer", "optional_highlight"]
	user_sections = ["direct_answer", "highlight"]

	if is_followup:
		answer_style = "followup_refinement"
		policy_mode = "followup_refinement"
		highlight_allowed = True
		implication_allowed = False
		recommendation_allowed = bool(analysis_requested)
		supporting_table_preference = "compact_table_when_requested"
		structure = ["direct_answer", "contextual_update", "optional_supporting_detail"]
		user_sections = ["direct_answer", "contextual_update", "supporting_detail"]
		if "bullet_points" not in preferred_formats:
			preferred_formats.append("bullet_points")
	elif _is_statement_question(text, tokens):
		answer_style = "statement_question"
		policy_mode = "statement_summary"
		highlight_allowed = True
		implication_allowed = bool(analysis_requested)
		recommendation_allowed = bool(analysis_requested)
		supporting_table_preference = "compact_when_helpful"
		structure = ["summary", "notable_line_items", "supporting_table"]
		user_sections = ["summary", "notable_line_items", "supporting_table"]
		if implication_allowed:
			structure.append("implication")
			user_sections.append("implication")
		for format_name in ("table", "bullet_points"):
			if format_name not in preferred_formats:
				preferred_formats.append(format_name)
	elif analysis_requested:
		answer_style = "analysis_question"
		policy_mode = "explicit_analysis"
		highlight_allowed = True
		implication_allowed = True
		recommendation_allowed = True
		supporting_table_preference = "support_with_grounded_breakdown"
		structure = ["direct_answer", "key_insight", "recommendation"]
		user_sections = ["direct_answer", "key_insight", "recommendation"]
		for format_name in ("bullet_points", "table"):
			if format_name not in preferred_formats:
				preferred_formats.append(format_name)
	elif _is_operational_list_question(tokens):
		answer_style = "operational_list"
		policy_mode = "operational_list"
		highlight_allowed = False
		implication_allowed = False
		recommendation_allowed = False
		supporting_table_preference = "compact_table_preferred"
		structure = ["direct_answer", "compact_summary", "document_list"]
		user_sections = ["direct_answer", "compact_summary", "document_list"]
		if "table" not in preferred_formats:
			preferred_formats.append("table")
	elif _is_ranking_or_trend_question(tokens):
		answer_style = "ranking_or_trend"
		policy_mode = "factual_summary"
		highlight_allowed = True
		implication_allowed = False
		recommendation_allowed = False
		supporting_table_preference = "compact_table_preferred"
		structure = ["direct_answer", "key_highlight", "supporting_table"]
		user_sections = ["direct_answer", "key_highlight", "supporting_table"]
		for format_name in ("table", "bullet_points"):
			if format_name not in preferred_formats:
				preferred_formats.append(format_name)
	elif preferred_formats:
		supporting_table_preference = "compact_table_when_requested" if "table" in preferred_formats else supporting_table_preference

	return {
		"policy_mode": policy_mode,
		"answer_style": answer_style,
		"direct_answer_first": True,
		"highlight_allowed": highlight_allowed,
		"implication_allowed": implication_allowed,
		"insight_allowed": True,
		"recommendation_allowed": recommendation_allowed,
		"supporting_table_preference": supporting_table_preference,
		"followup_conversational": followup_conversational,
		"grounding_rule": "Business interpretation and recommendations must be grounded in ERP facts or explicit derived calculations.",
		"structure": structure,
		"user_sections": user_sections,
		"preferred_formats": preferred_formats,
		"max_paragraph_sentences": 2,
	}
