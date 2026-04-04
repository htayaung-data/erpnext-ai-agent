from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set

from ai_assistant_ui.qwen_chat.metadata import (
	list_capability_specs,
	list_intent_class_specs,
	load_financial_summary_resolution_registry,
)


@dataclass(frozen=True)
class FinancialSummaryResolutionRegistryValidationResult:
	status: str
	errors: List[str]
	warnings: List[str]
	stats: Dict[str, Any]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_financial_summary_resolution_registry_validation",
			"contract_version": "1.0",
			"status": self.status,
			"errors": list(self.errors),
			"warnings": list(self.warnings),
			"stats": dict(self.stats),
		}


def _as_str_list(value: Any) -> List[str]:
	if not isinstance(value, list):
		return []
	return [str(item or "").strip() for item in value if str(item or "").strip()]


def _validate_allowed_membership(
	*,
	errors: List[str],
	label: str,
	values: List[str],
	allowed: Set[str],
) -> None:
	for value in values:
		if value not in allowed:
			errors.append(f"{label} references unknown value '{value}'.")


def validate_financial_summary_resolution_registry(
	payload: Dict[str, Any] | None = None,
) -> FinancialSummaryResolutionRegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_financial_summary_resolution_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")
	if str(data.get("intent_class") or "").strip() != "financial_summary":
		errors.append("intent_class must be 'financial_summary'.")

	known_intent_classes = {
		str(item.get("intent_class_id") or "").strip()
		for item in list_intent_class_specs()
		if isinstance(item, dict)
	}
	known_capabilities = {
		str(item.get("capability_id") or "").strip()
		for item in list_capability_specs()
		if isinstance(item, dict)
	}

	summary_domains = set(_as_str_list(data.get("summary_domains")))
	summary_focuses = set(_as_str_list(data.get("summary_focuses")))
	summary_metric_families = set(_as_str_list(data.get("summary_metric_families")))
	summary_grains = set(_as_str_list(data.get("summary_grains")))

	if not summary_domains:
		errors.append("summary_domains must be a non-empty list.")
	if not summary_focuses:
		errors.append("summary_focuses must be a non-empty list.")
	if not summary_metric_families:
		errors.append("summary_metric_families must be a non-empty list.")
	if not summary_grains:
		errors.append("summary_grains must be a non-empty list.")

	domain_rules = data.get("domain_rules")
	if not isinstance(domain_rules, list) or not domain_rules:
		errors.append("domain_rules must be a non-empty list.")
		domain_rules = []
	for idx, rule in enumerate(domain_rules):
		if not isinstance(rule, dict):
			errors.append(f"domain_rules[{idx}] must be an object.")
			continue
		source = str(rule.get("source") or "").strip()
		if source not in {"candidate_capability_ids", "ontology_concepts"}:
			errors.append(
				f"domain_rules[{idx}].source must be 'candidate_capability_ids' or 'ontology_concepts'."
			)
		match_any = _as_str_list(rule.get("match_any"))
		if not match_any:
			errors.append(f"domain_rules[{idx}].match_any must be a non-empty list.")
		if source == "candidate_capability_ids":
			_validate_allowed_membership(
				errors=errors,
				label=f"domain_rules[{idx}].match_any",
				values=match_any,
				allowed=known_capabilities,
			)
		emit_domain = str(rule.get("emit_domain") or "").strip()
		if emit_domain not in summary_domains:
			errors.append(f"domain_rules[{idx}].emit_domain must be one of summary_domains.")
		_validate_allowed_membership(
			errors=errors,
			label=f"domain_rules[{idx}].requires_metric_family_any",
			values=_as_str_list(rule.get("requires_metric_family_any")),
			allowed=summary_metric_families,
		)

	metric_family_rules = data.get("metric_family_rules")
	if not isinstance(metric_family_rules, list) or not metric_family_rules:
		errors.append("metric_family_rules must be a non-empty list.")
		metric_family_rules = []
	for idx, rule in enumerate(metric_family_rules):
		if not isinstance(rule, dict):
			errors.append(f"metric_family_rules[{idx}] must be an object.")
			continue
		if not _as_str_list(rule.get("canonical_metrics_any")):
			errors.append(f"metric_family_rules[{idx}].canonical_metrics_any must be a non-empty list.")
		emit_metric_family = str(rule.get("emit_metric_family") or "").strip()
		if emit_metric_family not in summary_metric_families:
			errors.append(
				f"metric_family_rules[{idx}].emit_metric_family must be one of summary_metric_families."
			)

	focus_rules = data.get("focus_rules")
	if not isinstance(focus_rules, list) or not focus_rules:
		errors.append("focus_rules must be a non-empty list.")
		focus_rules = []
	for idx, rule in enumerate(focus_rules):
		if not isinstance(rule, dict):
			errors.append(f"focus_rules[{idx}] must be an object.")
			continue
		source = str(rule.get("source") or "").strip()
		if source and source not in {"composite_profile_context"}:
			errors.append(
				f"focus_rules[{idx}].source must be 'composite_profile_context' when provided."
			)
		match_any = _as_str_list(rule.get("match_any"))
		if source and not match_any:
			errors.append(f"focus_rules[{idx}].match_any must be a non-empty list when source is provided.")
		_validate_allowed_membership(
			errors=errors,
			label=f"focus_rules[{idx}].requires_domains_all",
			values=_as_str_list(rule.get("requires_domains_all")),
			allowed=summary_domains,
		)
		required_metric_family = str(rule.get("requires_metric_family") or "").strip()
		if required_metric_family and required_metric_family not in summary_metric_families:
			errors.append(
				f"focus_rules[{idx}].requires_metric_family must be one of summary_metric_families."
			)
		emit_focus = str(rule.get("emit_focus") or "").strip()
		if emit_focus not in summary_focuses:
			errors.append(f"focus_rules[{idx}].emit_focus must be one of summary_focuses.")

	grain_rules = data.get("grain_rules")
	if not isinstance(grain_rules, list) or not grain_rules:
		errors.append("grain_rules must be a non-empty list.")
		grain_rules = []
	for idx, rule in enumerate(grain_rules):
		if not isinstance(rule, dict):
			errors.append(f"grain_rules[{idx}] must be an object.")
			continue
		if not _as_str_list(rule.get("requested_dimensions_any")):
			errors.append(f"grain_rules[{idx}].requested_dimensions_any must be a non-empty list.")
		emit_grain = str(rule.get("emit_grain") or "").strip()
		if emit_grain not in summary_grains:
			errors.append(f"grain_rules[{idx}].emit_grain must be one of summary_grains.")

	normalization_rules = data.get("normalization_rules")
	if not isinstance(normalization_rules, list) or not normalization_rules:
		errors.append("normalization_rules must be a non-empty list.")
		normalization_rules = []
	for idx, rule in enumerate(normalization_rules):
		if not isinstance(rule, dict):
			errors.append(f"normalization_rules[{idx}] must be an object.")
			continue
		_validate_allowed_membership(
			errors=errors,
			label=f"normalization_rules[{idx}].required_domains_all",
			values=_as_str_list(rule.get("required_domains_all")),
			allowed=summary_domains,
		)
		required_focus = str(rule.get("required_focus") or "").strip()
		if required_focus and required_focus not in summary_focuses:
			errors.append(f"normalization_rules[{idx}].required_focus must be one of summary_focuses.")
		decision = str(rule.get("decision") or "normalize_intent").strip() or "normalize_intent"
		if decision not in {"normalize_intent", "execute_composite"}:
			errors.append(
				f"normalization_rules[{idx}].decision must be 'normalize_intent' or 'execute_composite'."
			)
		target_intent_class = str(rule.get("target_intent_class") or "").strip()
		target_composite_plan_id = str(rule.get("target_composite_plan_id") or "").strip()
		if decision == "normalize_intent":
			if target_intent_class not in known_intent_classes:
				errors.append(
					f"normalization_rules[{idx}].target_intent_class references unknown intent_class '{target_intent_class}'."
				)
			if target_composite_plan_id:
				errors.append(
					f"normalization_rules[{idx}].target_composite_plan_id must be empty for normalize_intent rules."
				)
		if decision == "execute_composite":
			if not target_composite_plan_id:
				errors.append(
					f"normalization_rules[{idx}].target_composite_plan_id must be a non-empty string for execute_composite rules."
				)
			if target_intent_class:
				errors.append(
					f"normalization_rules[{idx}].target_intent_class must be empty for execute_composite rules."
				)
		if not str(rule.get("decision_reason") or "").strip():
			errors.append(f"normalization_rules[{idx}].decision_reason must be a non-empty string.")

	clarification_rules = data.get("clarification_rules")
	if not isinstance(clarification_rules, list) or not clarification_rules:
		errors.append("clarification_rules must be a non-empty list.")
		clarification_rules = []
	for idx, rule in enumerate(clarification_rules):
		if not isinstance(rule, dict):
			errors.append(f"clarification_rules[{idx}] must be an object.")
			continue
		if not str(rule.get("policy_id") or "").strip():
			errors.append(f"clarification_rules[{idx}].policy_id must be a non-empty string.")
		requires_domain_count = rule.get("requires_domain_count")
		if requires_domain_count is not None and (
			not isinstance(requires_domain_count, int) or int(requires_domain_count) < 0
		):
			errors.append(
				f"clarification_rules[{idx}].requires_domain_count must be a non-negative integer when provided."
			)
		requires_domain_count_min = rule.get("requires_domain_count_min")
		if requires_domain_count_min is not None and (
			not isinstance(requires_domain_count_min, int) or int(requires_domain_count_min) < 0
		):
			errors.append(
				f"clarification_rules[{idx}].requires_domain_count_min must be a non-negative integer when provided."
			)
		_validate_allowed_membership(
			errors=errors,
			label=f"clarification_rules[{idx}].requires_domains_all",
			values=_as_str_list(rule.get("requires_domains_all")),
			allowed=summary_domains,
		)
		_validate_allowed_membership(
			errors=errors,
			label=f"clarification_rules[{idx}].requires_domains_any",
			values=_as_str_list(rule.get("requires_domains_any")),
			allowed=summary_domains,
		)
		summary_focus_not_equal = str(rule.get("summary_focus_not_equal") or "").strip()
		if summary_focus_not_equal and summary_focus_not_equal not in summary_focuses:
			errors.append(
				f"clarification_rules[{idx}].summary_focus_not_equal must be one of summary_focuses."
			)
		if not str(rule.get("clarification_reason_type") or "").strip():
			errors.append(f"clarification_rules[{idx}].clarification_reason_type must be a non-empty string.")
		if not _as_str_list(rule.get("ambiguity_flags")):
			errors.append(f"clarification_rules[{idx}].ambiguity_flags must be a non-empty list.")
		if not str(rule.get("ambiguity_reason") or "").strip():
			errors.append(f"clarification_rules[{idx}].ambiguity_reason must be a non-empty string.")
		if not str(rule.get("decision_reason") or "").strip():
			errors.append(f"clarification_rules[{idx}].decision_reason must be a non-empty string.")
		if not isinstance(rule.get("blocks_legacy_fallback"), bool):
			errors.append(f"clarification_rules[{idx}].blocks_legacy_fallback must be a boolean.")

	policies = data.get("clarification_policies")
	if not isinstance(policies, dict):
		errors.append("clarification_policies must be an object.")
		policies = {}
	_validate_allowed_membership(
		errors=errors,
		label="clarification_policies.focus_required_domains",
		values=_as_str_list(policies.get("focus_required_domains")),
		allowed=summary_domains,
	)
	_validate_allowed_membership(
		errors=errors,
		label="clarification_policies.sales_domains",
		values=_as_str_list(policies.get("sales_domains")),
		allowed=summary_domains,
	)

	stats = {
		"domain_rule_count": len(domain_rules),
		"metric_family_rule_count": len(metric_family_rules),
		"focus_rule_count": len(focus_rules),
		"grain_rule_count": len(grain_rules),
		"normalization_rule_count": len(normalization_rules),
		"clarification_rule_count": len(clarification_rules),
		"summary_domain_count": len(summary_domains),
	}
	return FinancialSummaryResolutionRegistryValidationResult(
		status="fail" if errors else "pass",
		errors=errors,
		warnings=warnings,
		stats=stats,
	)
