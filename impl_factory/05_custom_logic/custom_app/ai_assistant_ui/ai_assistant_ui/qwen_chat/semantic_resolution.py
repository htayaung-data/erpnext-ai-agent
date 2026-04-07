from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	FinancialSummaryResolutionContract,
	FreshQueryInterpretationContract,
	SemanticResolutionContract,
	build_financial_summary_resolution_contract,
	build_fresh_query_interpretation_contract,
)
from ai_assistant_ui.qwen_chat.metadata import (
	capability_fresh_query_defaults,
	capability_ontology_concepts,
	list_financial_summary_clarification_rules,
	list_financial_summary_domain_rules,
	list_financial_summary_focus_rules,
	list_financial_summary_grain_rules,
	list_financial_summary_metric_family_rules,
	list_financial_summary_normalization_rules,
	report_capability_ids,
	load_semantic_resolution_registry,
	report_supported_metrics,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import get_canonical_key


@dataclass(frozen=True)
class SemanticResolutionOutcome:
	interpretation: FreshQueryInterpretationContract
	contract: Any
	clarification_reason_type: str = ""
	clarification_details: Dict[str, Any] = field(default_factory=dict)
	blocks_legacy_fallback: bool = False


def _clean_list(values: List[Any] | None) -> List[str]:
	return [str(value or "").strip() for value in (values or []) if str(value or "").strip()]


def _financial_statement_rules() -> List[Dict[str, Any]]:
	rules = load_semantic_resolution_registry().get("family_resolution_rules")
	if not isinstance(rules, list):
		return []
	return [
		dict(rule)
		for rule in rules
		if isinstance(rule, dict) and str(rule.get("intent_class") or "").strip() == "financial_statement"
	]


def _transaction_listing_rules() -> List[Dict[str, Any]]:
	rules = load_semantic_resolution_registry().get("family_resolution_rules")
	if not isinstance(rules, list):
		return []
	return [
		dict(rule)
		for rule in rules
		if isinstance(rule, dict) and str(rule.get("intent_class") or "").strip() == "transaction_listing"
	]


def resolve_financial_statement_interpretation(
	interpretation: FreshQueryInterpretationContract,
) -> SemanticResolutionOutcome | None:
	if str(interpretation.intent_class or "").strip() != "financial_statement":
		return None

	rules = _financial_statement_rules()
	report_to_rule: Dict[str, Dict[str, Any]] = {}
	for rule in rules:
		report_names = _clean_list(rule.get("candidate_reports"))
		if len(report_names) != 1:
			continue
		report_to_rule[report_names[0]] = rule

	current_reports = [
		report_name
		for report_name in _clean_list(interpretation.candidate_reports)
		if report_name in report_to_rule
	]
	current_reports = list(dict.fromkeys(current_reports))

	if len(current_reports) == 1:
		rule = report_to_rule[current_reports[0]]
		required_slots = rule.get("required_slots") if isinstance(rule.get("required_slots"), dict) else {}
		statement_variant = str(required_slots.get("statement_variant") or "").strip()
		resolved_interpretation = build_fresh_query_interpretation_contract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			intent_class=interpretation.intent_class,
			candidate_capability_ids=_clean_list(rule.get("candidate_capability_ids")),
			candidate_reports=_clean_list(rule.get("candidate_reports")),
			requested_dimensions=list(interpretation.requested_dimensions),
			requested_metrics=list(interpretation.requested_metrics),
			requested_time_scope=interpretation.requested_time_scope,
			target_limit=interpretation.target_limit,
			requested_presentation=list(interpretation.requested_presentation),
			extracted_slots=dict(interpretation.extracted_slots),
			ambiguity_flags=[
				flag for flag in _clean_list(interpretation.ambiguity_flags) if flag != "ambiguous_report"
			],
			ambiguity_reason="",
			confidence=float(interpretation.confidence or 0.0),
		)
		contract = SemanticResolutionContract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			intent_class="financial_statement",
			primary_business_area="financial",
			resolved_slots={"statement_variant": statement_variant},
			slot_confidence={"statement_variant": float(interpretation.confidence or 0.0)},
			candidate_family_ids=_clean_list(rule.get("candidate_family_ids")),
			candidate_capability_ids=_clean_list(rule.get("candidate_capability_ids")),
			candidate_reports=_clean_list(rule.get("candidate_reports")),
			ambiguity_flags=[],
			ambiguity_reason="",
			resolution_source={
				"intent_class": "semantic_runtime",
				"statement_variant": "semantic_runtime",
			},
			governed_decision=str(rule.get("governed_decision") or "execute").strip() or "execute",
			governed_reason="Financial statement variant resolved from the governed fresh-query interpretation contract.",
		)
		return SemanticResolutionOutcome(
			interpretation=resolved_interpretation,
			contract=contract,
		)

	candidate_reports = [
		report_name
		for rule in rules
		for report_name in _clean_list(rule.get("candidate_reports"))
	]
	candidate_reports = list(dict.fromkeys(candidate_reports))
	ambiguity_flags = list(dict.fromkeys(_clean_list(interpretation.ambiguity_flags) + ["ambiguous_report"]))
	resolved_interpretation = build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=["financial_statement_read"],
		candidate_reports=[],
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots),
		ambiguity_flags=ambiguity_flags,
		ambiguity_reason="Financial statement requests require an explicit governed statement variant before execution.",
		confidence=float(interpretation.confidence or 0.0),
	)
	contract = SemanticResolutionContract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class="financial_statement",
		primary_business_area="financial",
		resolved_slots={},
		slot_confidence={},
		candidate_family_ids=["financial_statement"],
		candidate_capability_ids=["financial_statement_read"],
		candidate_reports=candidate_reports,
		ambiguity_flags=["missing_statement_variant"],
		ambiguity_reason="Financial statement variant is unresolved.",
		resolution_source={
			"intent_class": "semantic_runtime",
			"statement_variant": "unresolved",
		},
		governed_decision="clarify",
		governed_reason="Financial statement routing must clarify the statement variant when the governed interpretation does not resolve a single statement.",
	)
	return SemanticResolutionOutcome(
		interpretation=resolved_interpretation,
		contract=contract,
	)


def resolve_transaction_listing_interpretation(
	interpretation: FreshQueryInterpretationContract,
) -> SemanticResolutionOutcome | None:
	if str(interpretation.intent_class or "").strip() != "transaction_listing":
		return None

	rules = _transaction_listing_rules()
	report_to_rule: Dict[str, Dict[str, Any]] = {}
	capability_to_rule: Dict[str, Dict[str, Any]] = {}
	for rule in rules:
		report_names = _clean_list(rule.get("candidate_reports"))
		if len(report_names) != 1:
			continue
		report_to_rule[report_names[0]] = rule
		candidate_capability_ids = _clean_list(rule.get("candidate_capability_ids"))
		if len(candidate_capability_ids) == 1:
			capability_to_rule[candidate_capability_ids[0]] = rule

	selected_rule: Dict[str, Any] | None = None
	resolution_source = "metadata_default"
	extracted_slots = (
		dict(interpretation.extracted_slots)
		if isinstance(interpretation.extracted_slots, dict)
		else {}
	)
	current_reports = [
		report_name
		for report_name in _clean_list(interpretation.candidate_reports)
		if report_name in report_to_rule
	]
	current_reports = list(dict.fromkeys(current_reports))
	if len(current_reports) == 1:
		selected_rule = report_to_rule[current_reports[0]]
		resolution_source = "semantic_runtime"
	else:
		listing_view = str(extracted_slots.get("listing_view") or "").strip()
		if listing_view:
			for rule in rules:
				required_slots = rule.get("required_slots") if isinstance(rule.get("required_slots"), dict) else {}
				if str(required_slots.get("listing_view") or "").strip() == listing_view:
					selected_rule = rule
					resolution_source = "semantic_runtime"
					break
	if selected_rule is None:
		current_capability_ids = [
			capability_id
			for capability_id in _clean_list(interpretation.candidate_capability_ids)
			if capability_id in capability_to_rule
		]
		current_capability_ids = list(dict.fromkeys(current_capability_ids))
		if len(current_capability_ids) == 1:
			selected_rule = capability_to_rule[current_capability_ids[0]]
			resolution_source = "semantic_runtime"
	if selected_rule is None:
		for rule in rules:
			required_slots = rule.get("required_slots") if isinstance(rule.get("required_slots"), dict) else {}
			if str(required_slots.get("listing_view") or "").strip() == "sales_invoice":
				selected_rule = rule
				break

	if selected_rule is None:
		return None

	selected_capability_ids = _clean_list(selected_rule.get("candidate_capability_ids"))
	selected_reports = _clean_list(selected_rule.get("candidate_reports"))
	selected_capability_id = selected_capability_ids[0] if selected_capability_ids else ""
	selected_report = selected_reports[0] if selected_reports else ""
	defaults = capability_fresh_query_defaults(selected_capability_id, intent_class="transaction_listing")
	requested_dimensions = (
		list(interpretation.requested_dimensions)
		or _clean_list(defaults.get("default_dimensions"))
		or report_supported_dimensions(selected_report)[:1]
	)
	requested_metrics = (
		list(interpretation.requested_metrics)
		or _clean_list(defaults.get("default_metrics"))
		or report_supported_metrics(selected_report)[:1]
	)
	required_slots = selected_rule.get("required_slots") if isinstance(selected_rule.get("required_slots"), dict) else {}
	listing_view = str(required_slots.get("listing_view") or "").strip()
	resolved_interpretation = build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=selected_capability_ids,
		candidate_reports=selected_reports,
		requested_dimensions=requested_dimensions,
		requested_metrics=requested_metrics,
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots),
		ambiguity_flags=[
			flag for flag in _clean_list(interpretation.ambiguity_flags) if flag != "ambiguous_report"
		],
		ambiguity_reason="",
		confidence=float(interpretation.confidence or 0.0),
	)
	contract = SemanticResolutionContract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class="transaction_listing",
		primary_business_area="transaction",
		resolved_slots={"listing_view": listing_view},
		slot_confidence={
			"listing_view": float(interpretation.confidence or 0.0) if resolution_source == "semantic_runtime" else 1.0
		},
		candidate_family_ids=_clean_list(selected_rule.get("candidate_family_ids")),
		candidate_capability_ids=selected_capability_ids,
		candidate_reports=selected_reports,
		ambiguity_flags=[],
		ambiguity_reason="",
		resolution_source={
			"intent_class": "semantic_runtime",
			"listing_view": resolution_source,
		},
		governed_decision=str(selected_rule.get("governed_decision") or "execute").strip() or "execute",
		governed_reason=(
			"Transaction-listing view resolved from the governed fresh-query interpretation contract."
			if resolution_source == "semantic_runtime"
			else "Transaction-listing view defaulted through governed metadata because the interpretation did not resolve a single governed document-listing target."
		),
	)
	return SemanticResolutionOutcome(
		interpretation=resolved_interpretation,
		contract=contract,
	)


def _inventory_summary_rules() -> List[Dict[str, Any]]:
	rules = load_semantic_resolution_registry().get("family_resolution_rules")
	if not isinstance(rules, list):
		return []
	return [
		dict(rule)
		for rule in rules
		if isinstance(rule, dict) and str(rule.get("intent_class") or "").strip() == "inventory_summary"
	]


def _aging_analysis_rules() -> List[Dict[str, Any]]:
	rules = load_semantic_resolution_registry().get("family_resolution_rules")
	if not isinstance(rules, list):
		return []
	return [
		dict(rule)
		for rule in rules
		if isinstance(rule, dict) and str(rule.get("intent_class") or "").strip() == "aging_analysis"
	]


def _trend_analysis_rules() -> List[Dict[str, Any]]:
	rules = load_semantic_resolution_registry().get("family_resolution_rules")
	if not isinstance(rules, list):
		return []
	return [
		dict(rule)
		for rule in rules
		if isinstance(rule, dict) and str(rule.get("intent_class") or "").strip() == "trend_analysis"
	]


def _trend_rule_metric(rule: Dict[str, Any]) -> str:
	required_slots = rule.get("required_slots") if isinstance(rule.get("required_slots"), dict) else {}
	return str(required_slots.get("trend_metric") or "").strip()


def _trend_rule_reports(rule: Dict[str, Any]) -> List[str]:
	return _clean_list(rule.get("candidate_reports"))


def _trend_rule_capabilities(rule: Dict[str, Any]) -> List[str]:
	return _clean_list(rule.get("candidate_capability_ids"))


def _select_trend_rule(
	*,
	rules: List[Dict[str, Any]],
	interpretation: FreshQueryInterpretationContract,
	trend_metric: str,
) -> tuple[Dict[str, Any] | None, str]:
	current_reports = list(dict.fromkeys(_clean_list(interpretation.candidate_reports)))
	current_capabilities = list(dict.fromkeys(_clean_list(interpretation.candidate_capability_ids)))
	default_reports_by_capability: Dict[str, str] = {}
	for capability_id in current_capabilities:
		defaults = capability_fresh_query_defaults(capability_id, intent_class="trend_analysis")
		default_report = str(defaults.get("default_report_name") or "").strip()
		if default_report:
			default_reports_by_capability[capability_id] = default_report

	def _score(rule: Dict[str, Any]) -> tuple[int, int, int, int]:
		rule_reports = set(_trend_rule_reports(rule))
		rule_capabilities = set(_trend_rule_capabilities(rule))
		report_match = int(bool(rule_reports & set(current_reports)))
		capability_match = int(bool(rule_capabilities & set(current_capabilities)))
		default_report_match = int(
			any(
				capability_id in rule_capabilities and report_name in rule_reports
				for capability_id, report_name in default_reports_by_capability.items()
			)
		)
		metric_default_match = int(_trend_rule_metric(rule) == "sales_amount")
		return (report_match, capability_match, default_report_match, metric_default_match)

	eligible = rules
	resolution_source = "metadata_default"
	if trend_metric:
		eligible = [rule for rule in rules if _trend_rule_metric(rule) == trend_metric]
		resolution_source = "semantic_runtime"
	if not eligible:
		return None, "unresolved"
	best_rule = max(eligible, key=_score)
	return best_rule, resolution_source


def _trend_requested_metrics(
	*,
	interpretation: FreshQueryInterpretationContract,
	selected_rule: Dict[str, Any],
	trend_metric: str,
) -> List[str]:
	report_name = str((_trend_rule_reports(selected_rule) or [""])[0] or "").strip()
	capability_id = str((_trend_rule_capabilities(selected_rule) or [""])[0] or "").strip()
	report_metrics = _clean_list(report_supported_metrics(report_name))
	requested_metrics = [
		metric for metric in list(interpretation.requested_metrics) if metric in report_metrics
	]
	if requested_metrics:
		return requested_metrics

	defaults = capability_fresh_query_defaults(capability_id, intent_class="trend_analysis")
	metric_overrides = (
		defaults.get("metric_overrides_by_canonical_key")
		if isinstance(defaults.get("metric_overrides_by_canonical_key"), dict)
		else {}
	)
	metric_candidates = _clean_list(metric_overrides.get(trend_metric))
	for metric in metric_candidates:
		if metric in report_metrics:
			return [metric]

	for metric in _clean_list(defaults.get("default_metrics")):
		if metric in report_metrics:
			return [metric]

	if trend_metric == "quantity":
		for metric in report_metrics:
			if "quantity" in metric.lower() or metric.lower() == "qty":
				return [metric]
	else:
		for metric in report_metrics:
			if "amount" in metric.lower() or "sales" in metric.lower() or "value" in metric.lower():
				return [metric]
	return report_metrics[:1]


def _ranking_rules() -> List[Dict[str, Any]]:
	rules = load_semantic_resolution_registry().get("family_resolution_rules")
	if not isinstance(rules, list):
		return []
	return [
		dict(rule)
		for rule in rules
		if isinstance(rule, dict) and str(rule.get("intent_class") or "").strip() == "ranked_entities"
	]


def _product_performance_rules() -> List[Dict[str, Any]]:
	rules = load_semantic_resolution_registry().get("family_resolution_rules")
	if not isinstance(rules, list):
		return []
	return [
		dict(rule)
		for rule in rules
		if isinstance(rule, dict) and str(rule.get("intent_class") or "").strip() == "product_performance"
	]


def _financial_summary_candidate_capability_ids(
	interpretation: FreshQueryInterpretationContract,
) -> List[str]:
	capability_ids = _clean_list(interpretation.candidate_capability_ids)
	for report_name in _clean_list(interpretation.candidate_reports):
		for capability_id in _clean_list(report_capability_ids(report_name)):
			if capability_id not in capability_ids:
				capability_ids.append(capability_id)
	return list(dict.fromkeys(capability_ids))


def _financial_summary_ontology_concepts(
	interpretation: FreshQueryInterpretationContract,
) -> List[str]:
	concepts: List[str] = []
	for capability_id in _financial_summary_candidate_capability_ids(interpretation):
		concepts.extend(_clean_list(capability_ontology_concepts(capability_id)))
	return list(dict.fromkeys(concepts))


def _financial_summary_domain_signals(
	interpretation: FreshQueryInterpretationContract,
	*,
	metric_family: str,
) -> List[str]:
	capability_domains: List[str] = []
	ontology_domains: List[str] = []
	candidate_capability_ids = set(_financial_summary_candidate_capability_ids(interpretation))
	ontology_concepts = set(_financial_summary_ontology_concepts(interpretation))
	for rule in list_financial_summary_domain_rules():
		source = str(rule.get("source") or "").strip()
		match_any = set(_clean_list(rule.get("match_any")))
		emit_domain = str(rule.get("emit_domain") or "").strip()
		if not emit_domain or not match_any:
			continue
		required_metric_families = set(_clean_list(rule.get("requires_metric_family_any")))
		if required_metric_families and metric_family not in required_metric_families:
			continue
		if source == "candidate_capability_ids" and candidate_capability_ids & match_any:
			capability_domains.append(emit_domain)
		elif source == "ontology_concepts" and ontology_concepts & match_any:
			ontology_domains.append(emit_domain)
	capability_domains = list(dict.fromkeys(capability_domains))
	if capability_domains:
		return capability_domains
	return list(dict.fromkeys(ontology_domains))


def _financial_summary_metric_family(interpretation: FreshQueryInterpretationContract) -> str:
	canonical_metric_keys = set(_canonical_metric_keys(list(interpretation.requested_metrics)))
	for rule in list_financial_summary_metric_family_rules():
		match_any = set(_clean_list(rule.get("canonical_metrics_any")))
		emit_metric_family = str(rule.get("emit_metric_family") or "").strip()
		if emit_metric_family and canonical_metric_keys & match_any:
			return emit_metric_family
	return ""


def _financial_summary_focus(
	*,
	interpretation: FreshQueryInterpretationContract,
	domains: List[str],
	metric_family: str,
) -> str:
	domain_set = set(domains)
	extracted_slots = (
		dict(interpretation.extracted_slots)
		if isinstance(interpretation.extracted_slots, dict)
		else {}
	)
	composite_profile_context = set(
		_clean_list(extracted_slots.get("composite_profile_context"))
	)
	for rule in list_financial_summary_focus_rules():
		source = str(rule.get("source") or "").strip()
		if source != "composite_profile_context":
			continue
		match_any = set(_clean_list(rule.get("match_any")))
		emit_focus = str(rule.get("emit_focus") or "").strip()
		if emit_focus and match_any and composite_profile_context & match_any:
			return emit_focus
	for rule in list_financial_summary_focus_rules():
		source = str(rule.get("source") or "").strip()
		if source == "composite_profile_context":
			continue
		requires_domains_all = set(_clean_list(rule.get("requires_domains_all")))
		requires_metric_family = str(rule.get("requires_metric_family") or "").strip()
		emit_focus = str(rule.get("emit_focus") or "").strip()
		if requires_domains_all and not requires_domains_all.issubset(domain_set):
			continue
		if requires_metric_family and metric_family != requires_metric_family:
			continue
		if emit_focus:
			return emit_focus
	return ""


def _financial_summary_grain(interpretation: FreshQueryInterpretationContract) -> str:
	requested_dimensions = set(_clean_list(interpretation.requested_dimensions))
	for rule in list_financial_summary_grain_rules():
		match_any = set(_clean_list(rule.get("requested_dimensions_any")))
		emit_grain = str(rule.get("emit_grain") or "").strip()
		if emit_grain and requested_dimensions & match_any:
			return emit_grain
	return ""


def _financial_summary_normalization_rule(
	*,
	domains: List[str],
	summary_focus: str,
) -> Dict[str, Any]:
	domain_set = set(domains)
	for rule in list_financial_summary_normalization_rules():
		required_domains_all = set(_clean_list(rule.get("required_domains_all")))
		required_focus = str(rule.get("required_focus") or "").strip()
		if required_domains_all and not required_domains_all.issubset(domain_set):
			continue
		if required_focus and summary_focus != required_focus:
			continue
		return dict(rule)
	return {}


def _financial_summary_clarification_rule(
	*,
	domains: List[str],
	summary_focus: str,
) -> Dict[str, Any]:
	domain_set = set(domains)
	for rule in list_financial_summary_clarification_rules():
		requires_domain_count = rule.get("requires_domain_count")
		requires_domain_count_min = rule.get("requires_domain_count_min")
		requires_domains_all = set(_clean_list(rule.get("requires_domains_all")))
		requires_domains_any = set(_clean_list(rule.get("requires_domains_any")))
		requires_focus_missing = bool(rule.get("requires_focus_missing"))
		summary_focus_not_equal = str(rule.get("summary_focus_not_equal") or "").strip()
		if requires_domain_count is not None and len(domains) != int(requires_domain_count):
			continue
		if requires_domain_count_min is not None and len(domains) < int(requires_domain_count_min):
			continue
		if requires_domains_all and not requires_domains_all.issubset(domain_set):
			continue
		if requires_domains_any and not (requires_domains_any & domain_set):
			continue
		if requires_focus_missing and summary_focus:
			continue
		if summary_focus_not_equal and summary_focus == summary_focus_not_equal:
			continue
		return dict(rule)
	return {}


def resolve_financial_summary_interpretation(
	interpretation: FreshQueryInterpretationContract,
) -> SemanticResolutionOutcome | None:
	if str(interpretation.intent_class or "").strip() != "financial_summary":
		return None

	candidate_capability_ids = _financial_summary_candidate_capability_ids(interpretation)
	candidate_reports = _clean_list(interpretation.candidate_reports)
	metric_family = _financial_summary_metric_family(interpretation)
	resolved_domains = _financial_summary_domain_signals(
		interpretation,
		metric_family=metric_family,
	)
	if not resolved_domains:
		clarification_rule = _financial_summary_clarification_rule(
			domains=[],
			summary_focus="",
		)
		if not clarification_rule:
			return None
		contract = build_financial_summary_resolution_contract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			resolved_summary_domains=[],
			resolved_summary_focus="",
			resolved_summary_metric_family=metric_family,
			resolved_summary_grain="",
			resolved_time_scope=interpretation.requested_time_scope,
			decision="clarify",
			ambiguity_flags=_clean_list(clarification_rule.get("ambiguity_flags")),
			ambiguity_reason=str(clarification_rule.get("ambiguity_reason") or "").strip(),
			decision_reason=str(clarification_rule.get("decision_reason") or "").strip(),
			candidate_capability_ids=candidate_capability_ids,
			candidate_reports=candidate_reports,
		)
		return SemanticResolutionOutcome(
			interpretation=interpretation,
			contract=contract,
			clarification_reason_type=str(clarification_rule.get("clarification_reason_type") or "").strip(),
			clarification_details={
				"financial_summary_resolution_contract": contract.to_payload(),
				"candidate_capability_ids": list(candidate_capability_ids),
				"candidate_reports": list(candidate_reports),
			},
			blocks_legacy_fallback=bool(clarification_rule.get("blocks_legacy_fallback")),
		)
	summary_focus = _financial_summary_focus(
		interpretation=interpretation,
		domains=resolved_domains,
		metric_family=metric_family,
	)
	if len(resolved_domains) != 1 and summary_focus != "cross_domain_health":
		clarification_rule = _financial_summary_clarification_rule(
			domains=resolved_domains,
			summary_focus="",
		)
		if not clarification_rule:
			return None
		contract = build_financial_summary_resolution_contract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			resolved_summary_domains=resolved_domains,
			resolved_summary_focus="",
			resolved_summary_metric_family=metric_family,
			resolved_summary_grain="",
			resolved_time_scope=interpretation.requested_time_scope,
			decision="clarify",
			ambiguity_flags=_clean_list(clarification_rule.get("ambiguity_flags")),
			ambiguity_reason=str(clarification_rule.get("ambiguity_reason") or "").strip(),
			decision_reason=str(clarification_rule.get("decision_reason") or "").strip(),
			candidate_capability_ids=candidate_capability_ids,
			candidate_reports=candidate_reports,
		)
		return SemanticResolutionOutcome(
			interpretation=interpretation,
			contract=contract,
			clarification_reason_type=str(clarification_rule.get("clarification_reason_type") or "").strip(),
			clarification_details={
				"financial_summary_resolution_contract": contract.to_payload(),
				"candidate_capability_ids": list(candidate_capability_ids),
				"candidate_reports": list(candidate_reports),
			},
			blocks_legacy_fallback=bool(clarification_rule.get("blocks_legacy_fallback")),
		)

	summary_grain = _financial_summary_grain(interpretation)

	clarification_rule = _financial_summary_clarification_rule(
		domains=resolved_domains,
		summary_focus=summary_focus,
	)

	if clarification_rule:
		contract = build_financial_summary_resolution_contract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			resolved_summary_domains=resolved_domains,
			resolved_summary_focus="",
			resolved_summary_metric_family=metric_family,
			resolved_summary_grain=summary_grain,
			resolved_time_scope=interpretation.requested_time_scope,
			decision="clarify",
			ambiguity_flags=_clean_list(clarification_rule.get("ambiguity_flags")),
			ambiguity_reason=str(clarification_rule.get("ambiguity_reason") or "").strip(),
			decision_reason=str(clarification_rule.get("decision_reason") or "").strip(),
			candidate_capability_ids=candidate_capability_ids,
			candidate_reports=candidate_reports,
		)
		return SemanticResolutionOutcome(
			interpretation=interpretation,
			contract=contract,
			clarification_reason_type=str(clarification_rule.get("clarification_reason_type") or "").strip(),
			clarification_details={
				"financial_summary_resolution_contract": contract.to_payload(),
				"candidate_capability_ids": list(candidate_capability_ids),
				"candidate_reports": list(candidate_reports),
			},
			blocks_legacy_fallback=bool(clarification_rule.get("blocks_legacy_fallback")),
		)

	normalization_rule = _financial_summary_normalization_rule(
		domains=resolved_domains,
		summary_focus=summary_focus,
	)
	decision = str(normalization_rule.get("decision") or "normalize_intent").strip() or "normalize_intent"
	target_intent_class = str(normalization_rule.get("target_intent_class") or "").strip()
	target_composite_plan_id = str(normalization_rule.get("target_composite_plan_id") or "").strip()
	if decision == "execute_composite" and target_composite_plan_id:
		resolved_extracted_slots = (
			dict(interpretation.extracted_slots)
			if isinstance(interpretation.extracted_slots, dict)
			else {}
		)
		contract = build_financial_summary_resolution_contract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			resolved_summary_domains=resolved_domains,
			resolved_summary_focus=summary_focus,
			resolved_summary_metric_family=metric_family,
			resolved_summary_grain=summary_grain,
			resolved_time_scope=interpretation.requested_time_scope,
			decision="execute_composite",
			target_composite_plan_id=target_composite_plan_id,
			ambiguity_flags=[],
			ambiguity_reason="",
			decision_reason=str(normalization_rule.get("decision_reason") or "").strip(),
			candidate_capability_ids=candidate_capability_ids,
			candidate_reports=candidate_reports,
		)
		resolved_extracted_slots["composite_profile_context"] = [target_composite_plan_id]
		resolved_extracted_slots["financial_summary_resolution_contract"] = contract.to_payload()
		resolved_interpretation = build_fresh_query_interpretation_contract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			intent_class=interpretation.intent_class,
			candidate_capability_ids=list(candidate_capability_ids),
			candidate_reports=list(candidate_reports),
			requested_dimensions=list(interpretation.requested_dimensions),
			requested_metrics=list(interpretation.requested_metrics),
			requested_time_scope=interpretation.requested_time_scope,
			target_limit=interpretation.target_limit,
			requested_presentation=list(interpretation.requested_presentation),
			extracted_slots=resolved_extracted_slots,
			ambiguity_flags=list(interpretation.ambiguity_flags),
			ambiguity_reason=str(interpretation.ambiguity_reason or "").strip(),
			confidence=float(interpretation.confidence or 0.0),
		)
		return SemanticResolutionOutcome(
			interpretation=resolved_interpretation,
			contract=contract,
		)
	if not target_intent_class:
		return None

	normalized_interpretation = build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=target_intent_class,
		candidate_capability_ids=list(candidate_capability_ids),
		candidate_reports=list(candidate_reports),
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots),
		ambiguity_flags=list(interpretation.ambiguity_flags),
		ambiguity_reason=str(interpretation.ambiguity_reason or "").strip(),
		confidence=float(interpretation.confidence or 0.0),
	)
	contract = build_financial_summary_resolution_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		resolved_summary_domains=resolved_domains,
		resolved_summary_focus=summary_focus,
		resolved_summary_metric_family=metric_family,
		resolved_summary_grain=summary_grain,
		resolved_time_scope=interpretation.requested_time_scope,
		decision=decision,
		target_intent_class=target_intent_class,
		ambiguity_flags=[],
		ambiguity_reason="",
		decision_reason=str(normalization_rule.get("decision_reason") or "").strip(),
		candidate_capability_ids=candidate_capability_ids,
		candidate_reports=candidate_reports,
	)
	return SemanticResolutionOutcome(
		interpretation=normalized_interpretation,
		contract=contract,
	)


def _normalize_slot_alias(text: str) -> str:
	return " ".join(str(text or "").strip().lower().split())


def _registry_alias_maps() -> Dict[str, List[Dict[str, Any]]]:
	value = load_semantic_resolution_registry().get("alias_maps")
	return value if isinstance(value, dict) else {}


def _resolve_slot_value_from_registry(slot_name: str, values: List[str]) -> str:
	alias_entries = _registry_alias_maps().get(slot_name)
	if not isinstance(alias_entries, list):
		return ""
	normalized_values = {
		_normalize_slot_alias(value)
		for value in _clean_list(values)
		if _normalize_slot_alias(value)
	}
	if not normalized_values:
		return ""
	for entry in alias_entries:
		if not isinstance(entry, dict):
			continue
		canonical_value = str(entry.get("canonical_value") or "").strip()
		aliases = {
			_normalize_slot_alias(alias)
			for alias in _clean_list(entry.get("aliases"))
			if _normalize_slot_alias(alias)
		}
		if canonical_value and aliases & normalized_values:
			return canonical_value
	return ""


def _resolve_ranking_metric(values: List[str]) -> str:
	metric = _resolve_slot_value_from_registry("ranking_metric", values)
	ranking_metric_keys: List[str] = []
	for value in _clean_list(values):
		canonical = get_canonical_key(value, dimension_or_metric="metric")
		if canonical in {"sales_amount", "quantity", "gross_profit", "outstanding_total"}:
			ranking_metric_keys.append(canonical)
	unique_metric_keys = list(dict.fromkeys(ranking_metric_keys))
	if metric and not unique_metric_keys:
		return metric
	if metric and unique_metric_keys == [metric]:
		return metric
	if len(unique_metric_keys) == 1:
		return unique_metric_keys[0]
	return ""


def _canonical_metric_keys(values: List[str]) -> List[str]:
	keys: List[str] = []
	for value in _clean_list(values):
		canonical = get_canonical_key(value, dimension_or_metric="metric")
		if canonical:
			keys.append(canonical)
	return list(dict.fromkeys(keys))


def resolve_inventory_summary_interpretation(
	interpretation: FreshQueryInterpretationContract,
) -> SemanticResolutionOutcome | None:
	if str(interpretation.intent_class or "").strip() != "inventory_summary":
		return None

	rules = _inventory_summary_rules()
	report_to_rule: Dict[str, Dict[str, Any]] = {}
	for rule in rules:
		report_names = _clean_list(rule.get("candidate_reports"))
		if len(report_names) != 1:
			continue
		report_to_rule[report_names[0]] = rule

	requested_dimensions = {value.lower(): value for value in _clean_list(interpretation.requested_dimensions)}
	axis_from_dimensions = ""
	if "warehouse" in requested_dimensions:
		axis_from_dimensions = "warehouse"
	elif "item" in requested_dimensions:
		axis_from_dimensions = "item"

	current_reports = [
		report_name
		for report_name in _clean_list(interpretation.candidate_reports)
		if report_name in report_to_rule
	]
	current_reports = list(dict.fromkeys(current_reports))

	selected_rule: Dict[str, Any] | None = None
	if len(current_reports) == 1:
		selected_rule = report_to_rule[current_reports[0]]
	elif axis_from_dimensions:
		for rule in rules:
			required_slots = rule.get("required_slots") if isinstance(rule.get("required_slots"), dict) else {}
			if str(required_slots.get("inventory_axis") or "").strip() == axis_from_dimensions:
				selected_rule = rule
				break
	else:
		for rule in rules:
			required_slots = rule.get("required_slots") if isinstance(rule.get("required_slots"), dict) else {}
			if str(required_slots.get("inventory_axis") or "").strip() == "item":
				selected_rule = rule
				break

	if selected_rule is None:
		return None

	required_slots = selected_rule.get("required_slots") if isinstance(selected_rule.get("required_slots"), dict) else {}
	inventory_axis = str(required_slots.get("inventory_axis") or "").strip()
	resolution_source = "semantic_runtime" if (len(current_reports) == 1 or axis_from_dimensions) else "metadata_default"
	resolved_interpretation = build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=_clean_list(selected_rule.get("candidate_capability_ids")),
		candidate_reports=_clean_list(selected_rule.get("candidate_reports")),
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots),
		ambiguity_flags=[
			flag for flag in _clean_list(interpretation.ambiguity_flags) if flag != "ambiguous_report"
		],
		ambiguity_reason="",
		confidence=float(interpretation.confidence or 0.0),
	)
	contract = SemanticResolutionContract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class="inventory_summary",
		primary_business_area="inventory",
		resolved_slots={"inventory_axis": inventory_axis},
		slot_confidence={
			"inventory_axis": float(interpretation.confidence or 0.0) if resolution_source == "semantic_runtime" else 1.0
		},
		candidate_family_ids=_clean_list(selected_rule.get("candidate_family_ids")),
		candidate_capability_ids=_clean_list(selected_rule.get("candidate_capability_ids")),
		candidate_reports=_clean_list(selected_rule.get("candidate_reports")),
		ambiguity_flags=[],
		ambiguity_reason="",
		resolution_source={
			"intent_class": "semantic_runtime",
			"inventory_axis": resolution_source,
		},
		governed_decision=str(selected_rule.get("governed_decision") or "execute").strip() or "execute",
		governed_reason=(
			"Inventory axis resolved from the governed fresh-query interpretation contract."
			if resolution_source == "semantic_runtime"
			else "Inventory axis defaulted through governed metadata because the interpretation did not resolve an explicit axis."
		),
	)
	return SemanticResolutionOutcome(
		interpretation=resolved_interpretation,
		contract=contract,
	)


def resolve_aging_analysis_interpretation(
	interpretation: FreshQueryInterpretationContract,
) -> SemanticResolutionOutcome | None:
	if str(interpretation.intent_class or "").strip() != "aging_analysis":
		return None

	rules = _aging_analysis_rules()
	report_to_rule: Dict[str, Dict[str, Any]] = {}
	capability_to_rule: Dict[str, Dict[str, Any]] = {}
	for rule in rules:
		report_names = _clean_list(rule.get("candidate_reports"))
		if len(report_names) == 1:
			report_to_rule[report_names[0]] = rule
		capability_ids = _clean_list(rule.get("candidate_capability_ids"))
		if len(capability_ids) == 1:
			capability_to_rule[capability_ids[0]] = rule

	current_reports = [
		report_name
		for report_name in _clean_list(interpretation.candidate_reports)
		if report_name in report_to_rule
	]
	current_reports = list(dict.fromkeys(current_reports))
	current_capability_ids = [
		capability_id
		for capability_id in _clean_list(interpretation.candidate_capability_ids)
		if capability_id in capability_to_rule
	]
	current_capability_ids = list(dict.fromkeys(current_capability_ids))

	selected_rule: Dict[str, Any] | None = None
	resolution_source = "unresolved"
	report_rule = report_to_rule.get(current_reports[0]) if len(current_reports) == 1 else None
	capability_rule = capability_to_rule.get(current_capability_ids[0]) if len(current_capability_ids) == 1 else None
	if report_rule is not None and capability_rule is not None:
		if report_rule == capability_rule:
			selected_rule = report_rule
			resolution_source = "semantic_runtime"
		else:
			selected_rule = None
	elif report_rule is not None:
		selected_rule = report_rule
		resolution_source = "semantic_runtime"
	elif capability_rule is not None:
		selected_rule = capability_rule
		resolution_source = "semantic_runtime"

	if selected_rule is not None:
		required_slots = selected_rule.get("required_slots") if isinstance(selected_rule.get("required_slots"), dict) else {}
		aging_view = str(required_slots.get("aging_view") or "").strip()
		resolved_interpretation = build_fresh_query_interpretation_contract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			intent_class=interpretation.intent_class,
			candidate_capability_ids=_clean_list(selected_rule.get("candidate_capability_ids")),
			candidate_reports=_clean_list(selected_rule.get("candidate_reports")),
			requested_dimensions=list(interpretation.requested_dimensions),
			requested_metrics=list(interpretation.requested_metrics),
			requested_time_scope=interpretation.requested_time_scope,
			target_limit=interpretation.target_limit,
			requested_presentation=list(interpretation.requested_presentation),
			extracted_slots=dict(interpretation.extracted_slots),
			ambiguity_flags=[
				flag for flag in _clean_list(interpretation.ambiguity_flags) if flag != "ambiguous_report"
			],
			ambiguity_reason="",
			confidence=float(interpretation.confidence or 0.0),
		)
		contract = SemanticResolutionContract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			intent_class="aging_analysis",
			primary_business_area="financial",
			resolved_slots={"aging_view": aging_view},
			slot_confidence={"aging_view": float(interpretation.confidence or 0.0)},
			candidate_family_ids=_clean_list(selected_rule.get("candidate_family_ids")),
			candidate_capability_ids=_clean_list(selected_rule.get("candidate_capability_ids")),
			candidate_reports=_clean_list(selected_rule.get("candidate_reports")),
			ambiguity_flags=[],
			ambiguity_reason="",
			resolution_source={
				"intent_class": "semantic_runtime",
				"aging_view": resolution_source,
			},
			governed_decision=str(selected_rule.get("governed_decision") or "execute").strip() or "execute",
			governed_reason="Aging view resolved from the governed fresh-query interpretation contract.",
		)
		return SemanticResolutionOutcome(
			interpretation=resolved_interpretation,
			contract=contract,
		)

	candidate_capability_ids = [
		capability_id
		for rule in rules
		for capability_id in _clean_list(rule.get("candidate_capability_ids"))
	]
	candidate_reports = [
		report_name
		for rule in rules
		for report_name in _clean_list(rule.get("candidate_reports"))
	]
	resolved_interpretation = build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(dict.fromkeys(candidate_capability_ids)),
		candidate_reports=[],
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots),
		ambiguity_flags=list(dict.fromkeys(_clean_list(interpretation.ambiguity_flags) + ["ambiguous_report"])),
		ambiguity_reason="Aging requests require a governed receivable or payable view before execution.",
		confidence=float(interpretation.confidence or 0.0),
	)
	contract = SemanticResolutionContract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class="aging_analysis",
		primary_business_area="financial",
		resolved_slots={},
		slot_confidence={},
		candidate_family_ids=["aging"],
		candidate_capability_ids=list(dict.fromkeys(candidate_capability_ids)),
		candidate_reports=list(dict.fromkeys(candidate_reports)),
		ambiguity_flags=["missing_aging_view"],
		ambiguity_reason="Aging view is unresolved.",
		resolution_source={
			"intent_class": "semantic_runtime",
			"aging_view": "unresolved",
		},
		governed_decision="clarify",
		governed_reason="Aging routing must clarify when the governed interpretation does not resolve a receivable or payable view.",
	)
	return SemanticResolutionOutcome(
		interpretation=resolved_interpretation,
		contract=contract,
	)


def resolve_trend_analysis_interpretation(
	interpretation: FreshQueryInterpretationContract,
) -> SemanticResolutionOutcome | None:
	if str(interpretation.intent_class or "").strip() != "trend_analysis":
		return None

	rules = _trend_analysis_rules()
	trend_metric = _resolve_ranking_metric(list(interpretation.requested_metrics))
	selected_rule, resolution_source = _select_trend_rule(
		rules=rules,
		interpretation=interpretation,
		trend_metric=trend_metric,
	)

	if selected_rule is None:
		return None

	trend_metric = trend_metric or _trend_rule_metric(selected_rule) or "sales_amount"
	requested_metrics = _trend_requested_metrics(
		interpretation=interpretation,
		selected_rule=selected_rule,
		trend_metric=trend_metric,
	)

	resolved_interpretation = build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=_clean_list(selected_rule.get("candidate_capability_ids")),
		candidate_reports=_clean_list(selected_rule.get("candidate_reports")),
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=requested_metrics,
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots),
		ambiguity_flags=[
			flag for flag in _clean_list(interpretation.ambiguity_flags) if flag != "ambiguous_report"
		],
		ambiguity_reason="",
		confidence=float(interpretation.confidence or 0.0),
	)
	contract = SemanticResolutionContract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class="trend_analysis",
		primary_business_area="trend",
		resolved_slots={"trend_metric": trend_metric},
		slot_confidence={
			"trend_metric": float(interpretation.confidence or 0.0) if resolution_source == "semantic_runtime" else 1.0
		},
		candidate_family_ids=_clean_list(selected_rule.get("candidate_family_ids")),
		candidate_capability_ids=_clean_list(selected_rule.get("candidate_capability_ids")),
		candidate_reports=_clean_list(selected_rule.get("candidate_reports")),
		ambiguity_flags=[],
		ambiguity_reason="",
		resolution_source={
			"intent_class": "semantic_runtime",
			"trend_metric": resolution_source,
		},
		governed_decision=str(selected_rule.get("governed_decision") or "execute").strip() or "execute",
		governed_reason=(
			"Trend metric resolved from the governed fresh-query interpretation contract."
			if resolution_source == "semantic_runtime"
			else "Trend metric defaulted through governed metadata because the interpretation did not resolve an explicit trend measure."
		),
	)
	return SemanticResolutionOutcome(
		interpretation=resolved_interpretation,
		contract=contract,
	)


def resolve_ranked_entities_interpretation(
	interpretation: FreshQueryInterpretationContract,
) -> SemanticResolutionOutcome | None:
	if str(interpretation.intent_class or "").strip() != "ranked_entities":
		return None

	ranking_subject = _resolve_slot_value_from_registry(
		"ranking_subject",
		list(interpretation.requested_dimensions),
	)
	ranking_metric = _resolve_ranking_metric(list(interpretation.requested_metrics))
	rules = _ranking_rules()

	matching_rules: List[Dict[str, Any]] = []
	for rule in rules:
		required_slots = rule.get("required_slots") if isinstance(rule.get("required_slots"), dict) else {}
		if str(required_slots.get("ranking_subject") or "").strip() != ranking_subject:
			continue
		if str(required_slots.get("ranking_metric") or "").strip() != ranking_metric:
			continue
		matching_rules.append(rule)

	selected_rule: Dict[str, Any] | None = None
	if len(matching_rules) == 1:
		selected_rule = matching_rules[0]
	elif len(matching_rules) > 1:
		current_reports = set(_clean_list(interpretation.candidate_reports))
		for rule in matching_rules:
			if current_reports & set(_clean_list(rule.get("candidate_reports"))):
				selected_rule = rule
				break

	if selected_rule is not None:
		resolved_interpretation = build_fresh_query_interpretation_contract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			intent_class=interpretation.intent_class,
			candidate_capability_ids=_clean_list(selected_rule.get("candidate_capability_ids")),
			candidate_reports=_clean_list(selected_rule.get("candidate_reports")),
			requested_dimensions=list(interpretation.requested_dimensions),
			requested_metrics=list(interpretation.requested_metrics),
			requested_time_scope=interpretation.requested_time_scope,
			target_limit=interpretation.target_limit,
			requested_presentation=list(interpretation.requested_presentation),
			extracted_slots=dict(interpretation.extracted_slots),
			ambiguity_flags=[
				flag for flag in _clean_list(interpretation.ambiguity_flags) if flag != "ambiguous_report"
			],
			ambiguity_reason="",
			confidence=float(interpretation.confidence or 0.0),
		)
		contract = SemanticResolutionContract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			intent_class="ranked_entities",
			primary_business_area="ranking",
			resolved_slots={
				"ranking_subject": ranking_subject,
				"ranking_metric": ranking_metric,
			},
			slot_confidence={
				"ranking_subject": float(interpretation.confidence or 0.0),
				"ranking_metric": float(interpretation.confidence or 0.0),
			},
			candidate_family_ids=_clean_list(selected_rule.get("candidate_family_ids")),
			candidate_capability_ids=_clean_list(selected_rule.get("candidate_capability_ids")),
			candidate_reports=_clean_list(selected_rule.get("candidate_reports")),
			ambiguity_flags=[],
			ambiguity_reason="",
			resolution_source={
				"intent_class": "semantic_runtime",
				"ranking_subject": "semantic_runtime",
				"ranking_metric": "semantic_runtime",
			},
			governed_decision=str(selected_rule.get("governed_decision") or "execute").strip() or "execute",
			governed_reason="Ranking subject and metric resolved from the governed fresh-query interpretation contract.",
		)
		return SemanticResolutionOutcome(
			interpretation=resolved_interpretation,
			contract=contract,
		)

	resolved_interpretation = build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=[],
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots),
		ambiguity_flags=list(dict.fromkeys(_clean_list(interpretation.ambiguity_flags) + ["ambiguous_report"])),
		ambiguity_reason="Ranked business-entity requests require a governed subject and metric before execution.",
		confidence=float(interpretation.confidence or 0.0),
	)
	contract = SemanticResolutionContract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class="ranked_entities",
		primary_business_area="ranking",
		resolved_slots={
			"ranking_subject": ranking_subject,
			"ranking_metric": ranking_metric,
		},
		slot_confidence={},
		candidate_family_ids=["ranking_analytics"],
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=[],
		ambiguity_flags=[
			flag
			for flag, value in {
				"missing_ranking_subject": ranking_subject,
				"missing_ranking_metric": ranking_metric,
			}.items()
			if not value
		],
		ambiguity_reason="Ranking subject or metric is unresolved.",
		resolution_source={
			"intent_class": "semantic_runtime",
			"ranking_subject": "semantic_runtime" if ranking_subject else "unresolved",
			"ranking_metric": "semantic_runtime" if ranking_metric else "unresolved",
		},
		governed_decision="clarify",
		governed_reason="Ranking routing must clarify when the governed interpretation does not resolve both subject and metric.",
	)
	return SemanticResolutionOutcome(
		interpretation=resolved_interpretation,
		contract=contract,
	)


def resolve_product_performance_interpretation(
	interpretation: FreshQueryInterpretationContract,
) -> SemanticResolutionOutcome | None:
	if str(interpretation.intent_class or "").strip() != "product_performance":
		return None

	rules = _product_performance_rules()
	report_to_rule: Dict[str, Dict[str, Any]] = {}
	for rule in rules:
		report_names = _clean_list(rule.get("candidate_reports"))
		if len(report_names) != 1:
			continue
		report_to_rule[report_names[0]] = rule

	current_reports = [
		report_name
		for report_name in _clean_list(interpretation.candidate_reports)
		if report_name in report_to_rule
	]
	current_reports = list(dict.fromkeys(current_reports))

	selected_rule: Dict[str, Any] | None = None
	resolution_source = "unresolved"
	if len(current_reports) == 1:
		selected_rule = report_to_rule[current_reports[0]]
		resolution_source = "semantic_runtime"
	else:
		requested_metric_keys = set(_canonical_metric_keys(list(interpretation.requested_metrics)))
		profitability_metric_keys = set(_canonical_metric_keys(report_supported_metrics("Gross Profit")))
		sales_history_metric_keys = set(_canonical_metric_keys(report_supported_metrics("Item-wise Sales History")))
		if requested_metric_keys:
			if requested_metric_keys.issubset(profitability_metric_keys) and not requested_metric_keys.issubset(sales_history_metric_keys):
				selected_rule = report_to_rule.get("Gross Profit")
				resolution_source = "semantic_runtime"
			elif requested_metric_keys.issubset(sales_history_metric_keys) and not requested_metric_keys.issubset(profitability_metric_keys):
				selected_rule = report_to_rule.get("Item-wise Sales History")
				resolution_source = "semantic_runtime"

	if selected_rule is not None:
		required_slots = selected_rule.get("required_slots") if isinstance(selected_rule.get("required_slots"), dict) else {}
		performance_view = str(required_slots.get("performance_view") or "").strip()
		resolved_interpretation = build_fresh_query_interpretation_contract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			intent_class=interpretation.intent_class,
			candidate_capability_ids=_clean_list(selected_rule.get("candidate_capability_ids")),
			candidate_reports=_clean_list(selected_rule.get("candidate_reports")),
			requested_dimensions=list(interpretation.requested_dimensions),
			requested_metrics=list(interpretation.requested_metrics),
			requested_time_scope=interpretation.requested_time_scope,
			target_limit=interpretation.target_limit,
			requested_presentation=list(interpretation.requested_presentation),
			extracted_slots=dict(interpretation.extracted_slots),
			ambiguity_flags=[
				flag for flag in _clean_list(interpretation.ambiguity_flags) if flag != "ambiguous_report"
			],
			ambiguity_reason="",
			confidence=float(interpretation.confidence or 0.0),
		)
		contract = SemanticResolutionContract(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			intent_class="product_performance",
			primary_business_area="product",
			resolved_slots={"performance_view": performance_view},
			slot_confidence={"performance_view": float(interpretation.confidence or 0.0)},
			candidate_family_ids=_clean_list(selected_rule.get("candidate_family_ids")),
			candidate_capability_ids=_clean_list(selected_rule.get("candidate_capability_ids")),
			candidate_reports=_clean_list(selected_rule.get("candidate_reports")),
			ambiguity_flags=[],
			ambiguity_reason="",
			resolution_source={
				"intent_class": "semantic_runtime",
				"performance_view": resolution_source,
			},
			governed_decision=str(selected_rule.get("governed_decision") or "execute").strip() or "execute",
			governed_reason="Product-performance view resolved from the governed fresh-query interpretation contract.",
		)
		return SemanticResolutionOutcome(
			interpretation=resolved_interpretation,
			contract=contract,
		)

	resolved_interpretation = build_fresh_query_interpretation_contract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class=interpretation.intent_class,
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=[],
		requested_dimensions=list(interpretation.requested_dimensions),
		requested_metrics=list(interpretation.requested_metrics),
		requested_time_scope=interpretation.requested_time_scope,
		target_limit=interpretation.target_limit,
		requested_presentation=list(interpretation.requested_presentation),
		extracted_slots=dict(interpretation.extracted_slots),
		ambiguity_flags=list(dict.fromkeys(_clean_list(interpretation.ambiguity_flags) + ["ambiguous_report"])),
		ambiguity_reason="Product-performance requests require a governed performance view before execution.",
		confidence=float(interpretation.confidence or 0.0),
	)
	contract = SemanticResolutionContract(
		request_id=interpretation.request_id,
		session_id=interpretation.session_id,
		intent_class="product_performance",
		primary_business_area="product",
		resolved_slots={},
		slot_confidence={},
		candidate_family_ids=["product_profitability"],
		candidate_capability_ids=list(interpretation.candidate_capability_ids),
		candidate_reports=[],
		ambiguity_flags=["missing_performance_view"],
		ambiguity_reason="Product-performance view is unresolved.",
		resolution_source={
			"intent_class": "semantic_runtime",
			"performance_view": "unresolved",
		},
		governed_decision="clarify",
		governed_reason="Product-performance routing must clarify when the governed interpretation does not resolve a profitability or sales-history view.",
	)
	return SemanticResolutionOutcome(
		interpretation=resolved_interpretation,
		contract=contract,
	)


def resolve_interpretation_semantically(
	interpretation: FreshQueryInterpretationContract,
) -> SemanticResolutionOutcome | None:
	for resolver in (
		resolve_financial_summary_interpretation,
		resolve_transaction_listing_interpretation,
		resolve_financial_statement_interpretation,
		resolve_inventory_summary_interpretation,
		resolve_aging_analysis_interpretation,
		resolve_trend_analysis_interpretation,
		resolve_ranked_entities_interpretation,
		resolve_product_performance_interpretation,
	):
		outcome = resolver(interpretation)
		if outcome is not None:
			return outcome
	return None
