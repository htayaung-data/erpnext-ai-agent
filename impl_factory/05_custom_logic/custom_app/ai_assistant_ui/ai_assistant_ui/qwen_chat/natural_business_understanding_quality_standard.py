from __future__ import annotations

import re
from typing import Any, Dict, List

from .natural_business_understanding_contracts import ALLOWED_ACTION_DECISIONS
from .natural_business_understanding_front_controller_cases import (
	list_nbu_front_controller_baseline_cases,
)


NBU_BUSINESS_CONVERSATION_QUALITY_STANDARD_VERSION = "1.0"


USER_FACING_FORBIDDEN_TERMS = {
	"qwen",
	"contract",
	"runtime",
	"artifact",
	"shadow",
	"planner",
	"activation",
	"trace",
	"payload",
	"governed boundary",
	"governed evidence",
	"governed source",
	"policy artifact",
	"blocked_missing_policy",
	"approved_policy_artifact_required",
}


NBU_BUSINESS_CONVERSATION_QUALITY_RULES: List[Dict[str, Any]] = [
	{
		"rule_id": "quality_clear_business_question_routes_or_answers",
		"category": "intent_understanding",
		"requirement": "A clear business question must route to an approved ERP family or answer from available evidence.",
		"covered_failure_classes": ["wrong_family_selection", "composite_precedence", "multi_domain_understanding_gap"],
		"applies_to_actions": ["execute_fresh_governed_query", "execute_governed_requery", "answer_from_current_artifact"],
	},
	{
		"rule_id": "quality_context_resolvable_followup_resolves_target",
		"category": "context_resolution",
		"requirement": "A vague but context-resolvable follow-up must resolve the intended table, row, entity, or prior result before answering.",
		"covered_failure_classes": [
			"row_reference_failure",
			"previous_artifact_resolution_failure",
			"wrong_latest_context_used",
			"selected_entity_carryover_gap",
		],
		"applies_to_actions": ["answer_from_current_artifact", "restore_previous_context", "execute_governed_requery"],
	},
	{
		"rule_id": "quality_ambiguous_context_asks_one_clarification",
		"category": "clarification",
		"requirement": "An ambiguous target must ask one useful clarification with business-readable options when possible.",
		"covered_failure_classes": ["ambiguous_reference_guess", "report_repeat_instead_of_clarification"],
		"applies_to_actions": ["ask_clarification", "show_supported_options"],
	},
	{
		"rule_id": "quality_missing_evidence_requeries_when_source_exists",
		"category": "evidence_planning",
		"requirement": "Missing current-result evidence should trigger an approved ERP requery when a compatible source exists.",
		"covered_failure_classes": ["missing_evidence_requery_gap"],
		"applies_to_actions": ["execute_governed_requery"],
	},
	{
		"rule_id": "quality_unsupported_evidence_explains_next_best_step",
		"category": "evidence_boundary",
		"requirement": "Unsupported evidence must explain what can be answered instead without pretending the missing data exists.",
		"covered_failure_classes": ["weak_authority_boundary", "generic_runtime_fallback"],
		"applies_to_actions": ["reject_with_boundary", "show_supported_options", "ask_clarification"],
	},
	{
		"rule_id": "quality_recommendation_prediction_policy_are_fact_separated",
		"category": "authority_boundary",
		"requirement": "Recommendations, predictions, approvals, and policy decisions must separate ERP facts from unauthorised decisions.",
		"covered_failure_classes": ["unsafe_recommendation", "unsafe_prediction"],
		"applies_to_actions": ["reject_with_boundary"],
	},
	{
		"rule_id": "quality_self_contained_request_clears_stale_context",
		"category": "context_isolation",
		"requirement": "A clear self-contained request or correction must not be trapped by stale context or pending ambiguity.",
		"covered_failure_classes": ["stale_context_leakage", "fresh_query_isolation", "correction_intent_failure"],
		"applies_to_actions": ["execute_fresh_governed_query", "clear_pending_context"],
	},
	{
		"rule_id": "quality_explanation_not_report_repeat",
		"category": "response_relevance",
		"requirement": "When the user asks for an explanation, do not repeat the whole table unless the requested explanation requires it.",
		"covered_failure_classes": ["definition_fallback_instead_of_row_answer", "generic_report_repeat"],
		"applies_to_actions": ["answer_from_current_artifact", "reject_with_boundary", "ask_clarification"],
	},
	{
		"rule_id": "quality_presentation_transform_preserves_facts",
		"category": "response_presentation",
		"requirement": "A presentation-only request may make the prior answer easier to read but must not add new ERP facts.",
		"covered_failure_classes": ["formatting_request_wrong_clarification"],
		"applies_to_actions": ["reformat_previous_answer"],
	},
	{
		"rule_id": "quality_no_internal_vocabulary_user_facing",
		"category": "response_language",
		"requirement": "User-facing answers must use business language and must not expose internal architecture vocabulary.",
		"covered_failure_classes": ["generic_runtime_fallback"],
		"applies_to_actions": sorted(ALLOWED_ACTION_DECISIONS),
	},
	{
		"rule_id": "quality_no_fake_confidence",
		"category": "truthfulness",
		"requirement": "If evidence, policy, or context is missing, the assistant must say so clearly instead of implying certainty.",
		"covered_failure_classes": ["weak_authority_boundary", "missing_evidence_requery_gap"],
		"applies_to_actions": ["reject_with_boundary", "ask_clarification", "show_supported_options"],
	},
	{
		"rule_id": "quality_out_of_scope_redirects_to_erp",
		"category": "scope_boundary",
		"requirement": "Out-of-scope requests must politely explain the limit and guide the user back to ERP/business questions.",
		"covered_failure_classes": [],
		"applies_to_actions": ["out_of_scope_response"],
	},
	{
		"rule_id": "quality_capability_guidance_is_business_readable",
		"category": "capability_guidance",
		"requirement": "Capability answers must describe business tasks the assistant can help with, not internal families or engines.",
		"covered_failure_classes": [],
		"applies_to_actions": ["answer_capability_question"],
	},
]


NBU_ACTION_QUALITY_EXPECTATIONS: Dict[str, List[str]] = {
	"answer_from_current_artifact": [
		"resolve_context_target",
		"verify_visible_evidence",
		"answer_with_specific_facts",
		"avoid_table_repeat_unless_requested",
	],
	"reformat_previous_answer": [
		"reuse_prior_answer_only",
		"preserve_business_facts",
		"make_readability_better",
		"avoid_internal_architecture_terms",
	],
	"execute_fresh_governed_query": [
		"select_best_business_family",
		"validate_registry_target",
		"clear_stale_context_when_self_contained",
	],
	"execute_governed_requery": [
		"carry_resolved_entity",
		"validate_approved_source",
		"request_missing_evidence_only",
	],
	"ask_clarification": [
		"ask_one_business_question",
		"show_options_when_available",
		"avoid_internal_terms",
	],
	"show_supported_options": [
		"show_business_readable_options",
		"avoid_internal_ids_when_labels_exist",
	],
	"restore_previous_context": [
		"resolve_requested_prior_context",
		"avoid_wrong_latest_context",
	],
	"clear_pending_context": [
		"honor_user_correction_or_cancellation",
		"do_not_keep_stale_ambiguity",
	],
	"reject_with_boundary": [
		"separate_facts_from_decision",
		"explain_missing_policy_or_evidence",
		"offer_safe_fact_based_next_step",
	],
	"answer_capability_question": [
		"describe_business_capabilities",
		"avoid_internal_architecture_terms",
	],
	"out_of_scope_response": [
		"explain_scope_limit",
		"redirect_to_erp_business_examples",
	],
	"observe_only": [
		"do_not_change_user_facing_behavior",
		"record_trace_for_evaluation",
	],
}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _normalize_text(value: Any) -> str:
	return re.sub(r"\s+", " ", _clean_text(value).lower()).strip()


def list_nbu_business_conversation_quality_rules() -> List[Dict[str, Any]]:
	return [dict(rule) for rule in NBU_BUSINESS_CONVERSATION_QUALITY_RULES]


def nbu_action_quality_expectations(action: str) -> List[str]:
	return list(NBU_ACTION_QUALITY_EXPECTATIONS.get(_clean_text(action), []))


def _covered_failure_classes() -> set[str]:
	return {
		str(value or "").strip()
		for rule in NBU_BUSINESS_CONVERSATION_QUALITY_RULES
		for value in rule.get("covered_failure_classes", [])
		if str(value or "").strip()
	}


def _baseline_failure_classes() -> set[str]:
	return {
		str(value or "").strip()
		for case in list_nbu_front_controller_baseline_cases()
		for value in case.get("failure_classes", [])
		if str(value or "").strip()
	}


def validate_nbu_business_conversation_quality_standard() -> Dict[str, Any]:
	errors: List[str] = []
	seen: set[str] = set()
	for index, rule in enumerate(NBU_BUSINESS_CONVERSATION_QUALITY_RULES):
		rule_id = _clean_text(rule.get("rule_id"))
		if not rule_id:
			errors.append(f"rule_{index}:missing_rule_id")
		elif rule_id in seen:
			errors.append(f"{rule_id}:duplicate_rule_id")
		seen.add(rule_id)
		for key in ("category", "requirement", "applies_to_actions"):
			if not rule.get(key):
				errors.append(f"{rule_id or 'rule_' + str(index)}:missing_{key}")
		for action in _clean_list(rule.get("applies_to_actions")):
			if action not in ALLOWED_ACTION_DECISIONS:
				errors.append(f"{rule_id}:unknown_action:{action}")

	for action in sorted(ALLOWED_ACTION_DECISIONS):
		if action not in NBU_ACTION_QUALITY_EXPECTATIONS:
			errors.append(f"missing_action_quality_expectations:{action}")

	missing_failure_classes = sorted(_baseline_failure_classes().difference(_covered_failure_classes()))
	for failure_class in missing_failure_classes:
		errors.append(f"baseline_failure_class_not_covered:{failure_class}")

	return {
		"ok": not errors,
		"schema_version": NBU_BUSINESS_CONVERSATION_QUALITY_STANDARD_VERSION,
		"rule_count": len(NBU_BUSINESS_CONVERSATION_QUALITY_RULES),
		"action_count": len(NBU_ACTION_QUALITY_EXPECTATIONS),
		"covered_failure_class_count": len(_covered_failure_classes()),
		"errors": errors,
	}


def validate_nbu_user_facing_response_text(response_payload: Dict[str, Any] | str) -> Dict[str, Any]:
	if isinstance(response_payload, str):
		text = response_payload
	else:
		response = _clean_dict(response_payload)
		parts = [
			_clean_text(response.get("title")),
			_clean_text(response.get("answer_text")),
			_clean_text(response.get("text")),
		]
		parts.extend(_clean_list(response.get("next_steps")))
		text = " ".join(part for part in parts if part)
	normalized = _normalize_text(text)
	violations = [
		term
		for term in sorted(USER_FACING_FORBIDDEN_TERMS)
		if term in normalized
	]
	return {
		"ok": not violations,
		"schema_version": NBU_BUSINESS_CONVERSATION_QUALITY_STANDARD_VERSION,
		"violations": violations,
		"checked_term_count": len(USER_FACING_FORBIDDEN_TERMS),
	}
