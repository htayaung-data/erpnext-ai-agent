from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Set

from ai_assistant_ui.qwen_chat.metadata import (
	capability_dimensions_for_report,
	governed_self_contained_business_terms,
	load_business_ontology,
	ontology_detect_concepts,
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


def _strip_leading_politeness(text: str) -> str:
	value = _normalize_text(text)
	for prefix in ("please ", "kindly ", "can you ", "could you ", "would you ", "for me "):
		if value.startswith(prefix):
			return value[len(prefix) :].strip()
	return value


@dataclass(frozen=True)
class FollowUpIntent:
	requested_modes: List[str]
	matched_aliases: Dict[str, List[str]]
	target_dimension: str = ""
	target_limit: int = 0
	sort_direction: str = ""
	target_metric: str = ""
	requested_columns: List[str] = field(default_factory=list)
	requested_time_scope: str = ""


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


def _detect_target_metric(text: str) -> str:
	if not text:
		return ""
	if "contribution percent" in text or "contribution %" in text or "contribution ratio" in text:
		return "contribution_percent"
	if "gross profit percent" in text or "gross profit percentage" in text or "margin percent" in text:
		return "gross_profit_percent"
	if "gross profit" in text:
		return "gross_profit"
	if "buying amount" in text or re.search(r"\bcost\b", text):
		return "buying_amount"
	if "revenue" in text or "sales amount" in text:
		return "sales_amount"
	if "outstanding amount" in text or "outstanding" in text:
		return "outstanding_total"
	if "total due" in text or "amount due" in text:
		return "total_due"
	if "balance value" in text or "stock value" in text:
		return "balance_value"
	if "balance qty" in text or "balance quantity" in text:
		return "balance_qty"
	if "quantity" in text or re.search(r"\bqty\b", text):
		return "quantity"
	if re.search(r"\bamount\b", text):
		return "amount"
	return ""


def _detect_requested_columns(text: str) -> List[str]:
	columns: List[str] = []
	if any(token in text for token in ("item name", "product name", "customer name", "supplier name", "with their", "with item", "with customer", "with supplier")):
		columns.append("entity")
	metric = _detect_target_metric(text)
	if metric:
		if metric == "amount":
			columns.append("amount")
		else:
			columns.append(metric)
	if "contribution percent" in text or "contribution %" in text:
		columns.append("contribution_percent")
	if "item code" in text:
		columns.append("entity_code")
	if "territory" in text:
		columns.append("territory")
	return list(dict.fromkeys([value for value in columns if value]))


def _detect_requested_time_scope(text: str) -> str:
	if "last month" in text or "previous month" in text:
		return "last_month"
	if "this month" in text or "current month" in text:
		return "current_period"
	if "all time" in text or "all period" in text or "overall" in text:
		return "all_period"
	if "as of now" in text or "as of today" in text or re.search(r"\bas of\b", text):
		return "as_of_today"
	return ""


def _detect_requested_presentation_modes(text: str) -> List[str]:
	modes: List[str] = []
	if any(phrase in text for phrase in ("with table", "as table", "in table", "show table", "tabular")) or re.search(r"\btable\b", text):
		modes.append("table_presentation")
	if any(
		phrase in text
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
		modes.append("bullet_presentation")
	return list(dict.fromkeys(modes))


def detect_followup_intent(message: str, language: str = "en", grounded_turn: Dict[str, object] | None = None) -> FollowUpIntent:
	text = _normalize_text(message)
	if not text:
		return FollowUpIntent(
			requested_modes=[],
			matched_aliases={},
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
		)
	entries = load_business_ontology().get("follow_up_classes")
	if not isinstance(entries, list):
		return FollowUpIntent(
			requested_modes=[],
			matched_aliases={},
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
		)

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

	target_metric = _detect_target_metric(text)
	if target_metric:
		requested_modes.append("metric_refinement")
		matched_aliases.setdefault("metric_refinement", []).append(target_metric)

	requested_columns = _detect_requested_columns(text)
	if requested_columns:
		requested_modes.append("column_refinement")
		matched_aliases.setdefault("column_refinement", []).extend(requested_columns)

	requested_time_scope = _detect_requested_time_scope(text)
	if requested_time_scope:
		requested_modes.append("time_scope_restatement")
		matched_aliases.setdefault("time_scope_restatement", []).append(requested_time_scope)

	for presentation_mode in _detect_requested_presentation_modes(text):
		if presentation_mode not in requested_modes:
			requested_modes.append(presentation_mode)
		matched_aliases.setdefault(presentation_mode, []).append(presentation_mode)

	return FollowUpIntent(
		requested_modes=list(dict.fromkeys(requested_modes)),
		matched_aliases=matched_aliases,
		target_dimension=target_dimension,
		target_limit=target_limit,
		sort_direction=sort_direction,
		target_metric=target_metric,
		requested_columns=requested_columns,
		requested_time_scope=requested_time_scope,
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
	normalized_text = _strip_leading_politeness(text)
	terms = governed_self_contained_business_terms(language)
	if len(normalized_text.split()) < 3:
		return False
	parsed = intent or detect_followup_intent(normalized_text, language=language, grounded_turn=grounded_turn)
	has_grounded_turn = bool(isinstance(grounded_turn, dict) and grounded_turn.get("grounded"))
	explicit_domain_anchor = bool(
		re.search(
			r"\b(customer|customers|supplier|suppliers|vendor|vendors|sale|sales|revenue|profit|invoice|invoices|product|products|item|items|inventory|stock|warehouse|warehouses|payable|payables|receivable|receivables|cash|balance|statement|trend|ar|ap)\b",
			normalized_text,
		)
	)
	prefixes = ontology_self_contained_prefixes(language)
	business_signals = any(_contains_alias(normalized_text, token) for token in terms)
	concept_hits = ontology_detect_concepts(normalized_text, language=language)
	if not business_signals and not concept_hits:
		business_signals = bool(
			re.search(r"\b(customer|customers|supplier|suppliers|vendor|vendors|staff|employee|employees|headcount)\b", normalized_text)
		)
	if has_grounded_turn:
		refinement_modes = {
			"presentation_transform",
			"table_presentation",
			"bullet_presentation",
			"sort_or_limit",
			"metric_refinement",
			"column_refinement",
			"time_scope_restatement",
		}
		if set(parsed.requested_modes).issubset(refinement_modes) and not explicit_domain_anchor:
			return False
	if len(normalized_text.split()) < 4 and not business_signals:
		return False
	strong_business_restatement = bool(
		(business_signals or explicit_domain_anchor)
		and len(normalized_text.split()) >= 5
		and (
			parsed.requested_time_scope
			or parsed.target_metric
			or bool(set(parsed.requested_modes).intersection({"sort_or_limit", "metric_refinement", "time_scope_restatement"}))
			or bool(re.search(r"\b(trend|statement|revenue|profit|balance|cash flow|inventory|customer|supplier|invoice|product|item)\b", normalized_text))
		)
	)
	if has_grounded_turn and "presentation_transform" in parsed.requested_modes and not strong_business_restatement:
		return False
	if has_grounded_turn and "dimension_breakdown" in parsed.requested_modes and len(text.split()) < 5 and not strong_business_restatement:
		return False
	if has_grounded_turn and "metric_refinement" in parsed.requested_modes and len(text.split()) < 6 and not strong_business_restatement:
		return False
	if has_grounded_turn and "column_refinement" in parsed.requested_modes and len(text.split()) < 6 and not strong_business_restatement:
		return False
	if has_grounded_turn and "bullet_presentation" in parsed.requested_modes and not strong_business_restatement:
		return False
	if has_grounded_turn and "time_scope_restatement" in parsed.requested_modes and not strong_business_restatement:
		return False
	if any(normalized_text.startswith(f"{prefix} ") or normalized_text == prefix for prefix in prefixes) and business_signals:
		return True
	if (
		business_signals
		and len(normalized_text.split()) >= 4
		and (
			parsed.requested_time_scope
			or parsed.target_metric
			or bool(set(parsed.requested_modes).intersection({"sort_or_limit", "metric_refinement", "time_scope_restatement"}))
			or bool(re.search(r"\b(trend|statement|revenue|profit|balance|cash flow|inventory|customer|supplier|staff|employee|headcount)\b", normalized_text))
		)
	):
		return True
	return False


def is_safe_local_compatibility_intent(
	message: str,
	language: str = "en",
	grounded_turn: Dict[str, object] | None = None,
) -> bool:
	parsed = detect_followup_intent(message, language=language, grounded_turn=grounded_turn)
	modes = set(parsed.requested_modes)
	if not modes:
		return False
	if not modes.issubset({"presentation_transform", "table_presentation", "bullet_presentation", "sort_or_limit", "metric_refinement", "column_refinement"}):
		return False
	if "sort_or_limit" in modes and not (parsed.target_limit or parsed.sort_direction):
		return False
	if "time_scope_restatement" in modes:
		return False
	return True


_SUPPORTED_DOMAIN_TERMS = {
	"finance": {"profit", "loss", "balance", "cash", "payable", "payables", "receivable", "receivables", "ar", "ap", "financial"},
	"sales": {"sales", "sale", "revenue", "trend", "customer", "customers", "invoice", "invoices"},
	"inventory": {"inventory", "stock", "warehouse", "warehouses"},
	"product": {"product", "products", "item", "items", "sku", "profitability", "gross", "margin"},
	"transaction": {"transaction", "transactions", "invoice", "invoices", "payment", "payments"},
}

_OUT_OF_SCOPE_DOMAIN_TERMS = {
	"hr": {"staff", "employee", "employees", "headcount", "payroll", "attendance", "leave", "salary slip"},
}


def _message_domain_hints(text: str) -> Set[str]:
	value = _normalize_text(text)
	if not value:
		return set()
	tokens = set(re.findall(r"[a-z0-9]+", value))
	domains: Set[str] = set()
	for domain, terms in _SUPPORTED_DOMAIN_TERMS.items():
		for term in terms:
			normalized_term = _normalize_text(term)
			if not normalized_term:
				continue
			term_tokens = normalized_term.split()
			if (len(term_tokens) == 1 and term_tokens[0] in tokens) or _contains_alias(value, normalized_term):
				domains.add(domain)
				break
	for domain, terms in _OUT_OF_SCOPE_DOMAIN_TERMS.items():
		for term in terms:
			normalized_term = _normalize_text(term)
			if not normalized_term:
				continue
			term_tokens = normalized_term.split()
			if (len(term_tokens) == 1 and term_tokens[0] in tokens) or _contains_alias(value, normalized_term):
				domains.add(domain)
				break
	return domains


def _grounded_context_domains(grounded_turn: Dict[str, object] | None) -> Set[str]:
	turn = grounded_turn if isinstance(grounded_turn, dict) else {}
	if not turn:
		return set()
	value = " ".join(
		part
		for part in [
			str(turn.get("artifact_family_id") or "").strip(),
			str(turn.get("source_name") or "").strip(),
			" ".join(str(item or "").strip() for item in (turn.get("dimensions") or []) if str(item or "").strip()),
			" ".join(str(item or "").strip() for item in (turn.get("metrics") or []) if str(item or "").strip()),
		]
		if part
	)
	domains = _message_domain_hints(value)
	if "aging" in _normalize_text(value):
		domains.update({"finance", "transaction"})
	if "financial_statement" in _normalize_text(value):
		domains.add("finance")
	if "ranking_analytics" in _normalize_text(value) or "trend_analytics" in _normalize_text(value):
		domains.add("sales")
	if "transaction_listing" in _normalize_text(value):
		domains.update({"transaction", "sales"})
	if "inventory_snapshot" in _normalize_text(value):
		domains.add("inventory")
	if "product_profitability" in _normalize_text(value):
		domains.add("product")
	return domains


def assess_context_isolation(
	message: str,
	*,
	language: str = "en",
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	text = _normalize_text(message)
	intent = detect_followup_intent(text, language=language, grounded_turn=grounded_turn)
	requested_modes = {str(mode or "").strip() for mode in (intent.requested_modes or []) if str(mode or "").strip()}
	local_only_modes = {
		"presentation_transform",
		"table_presentation",
		"bullet_presentation",
		"sort_or_limit",
		"metric_refinement",
		"column_refinement",
		"time_scope_restatement",
	}

	message_domains = _message_domain_hints(text)
	context_domains = _grounded_context_domains(grounded_turn)
	out_of_scope_domains = sorted(domain for domain in message_domains if domain in _OUT_OF_SCOPE_DOMAIN_TERMS)
	if out_of_scope_domains:
		return {
			"force_new_query": True,
			"out_of_scope": True,
			"reason": "The request targets a business domain outside the current governed Qwen ERP scope.",
			"requested_domains": sorted(message_domains),
			"context_domains": sorted(context_domains),
			"primary_domain": out_of_scope_domains[0],
		}

	self_contained = is_self_contained_business_request(
		message,
		language=language,
		intent=intent,
		grounded_turn=grounded_turn,
	)
	if requested_modes and requested_modes.issubset(local_only_modes) and not self_contained:
		return {
			"force_new_query": False,
			"out_of_scope": False,
			"reason": "",
			"requested_domains": sorted(message_domains),
			"context_domains": sorted(context_domains),
		}
	if self_contained:
		return {
			"force_new_query": True,
			"out_of_scope": False,
			"reason": "The request is self-contained and should be treated as a fresh governed ERP question.",
			"requested_domains": sorted(message_domains),
			"context_domains": sorted(context_domains),
		}

	if message_domains and context_domains and message_domains.isdisjoint(context_domains):
		return {
			"force_new_query": True,
			"out_of_scope": False,
			"reason": "The request shifts to a different governed business area and should not inherit the prior artifact.",
			"requested_domains": sorted(message_domains),
			"context_domains": sorted(context_domains),
		}

	return {
		"force_new_query": False,
		"out_of_scope": False,
		"reason": "",
		"requested_domains": sorted(message_domains),
		"context_domains": sorted(context_domains),
	}
