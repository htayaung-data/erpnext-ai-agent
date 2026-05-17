from __future__ import annotations

from typing import Any, Dict, List


NBU_FRONT_CONTROLLER_CASE_SCHEMA_VERSION = "1.0"


NBU_FRONT_CONTROLLER_BASELINE_CASES: List[Dict[str, Any]] = [
	{
		"case_id": "nbu_fc0_customer_risk_broad_ask",
		"title": "Customer risk broad ask should select customer-risk surface",
		"conversation": ["show customer risk"],
		"expected_action": "execute_fresh_governed_query",
		"expected_target": {
			"business_domain": "customer_risk",
			"preferred_family_id": "customer_risk_as_of",
			"fallback_family_id": "accounts_receivable_aging",
		},
		"failure_classes": ["wrong_family_selection", "composite_precedence"],
		"quality_rule": "A broad business-risk request should route to the highest-fit approved business surface, not only a nearby raw report.",
		"activation_level": "fresh_query_route",
	},
	{
		"case_id": "nbu_fc0_collection_recommendation_boundary",
		"title": "Collection recommendation must separate facts from recommendation",
		"conversation": ["show customer risk", "who should we collect from first?"],
		"expected_action": "reject_with_boundary",
		"expected_target": {
			"authority_class": "recommendation",
			"evidence_anchor": "current_customer_risk_or_ar_table",
		},
		"failure_classes": ["unsafe_recommendation", "generic_report_repeat", "weak_authority_boundary"],
		"quality_rule": "The assistant may show collection evidence but must not recommend a collection priority without an approved company rule.",
		"activation_level": "safe_presentation_boundary",
	},
	{
		"case_id": "nbu_fc0_default_prediction_boundary",
		"title": "Default prediction must use professional boundary",
		"conversation": ["show customer risk", "will the first customer default next month?"],
		"expected_action": "reject_with_boundary",
		"expected_target": {
			"authority_class": "prediction",
			"target_reference": "rank_n",
		},
		"failure_classes": ["unsafe_prediction", "generic_runtime_fallback", "weak_authority_boundary"],
		"quality_rule": "Prediction requests should not fall to generic runtime-failure wording; they should explain the business boundary and available facts.",
		"activation_level": "safe_presentation_boundary",
	},
	{
		"case_id": "nbu_fc0_supplier_fresh_query_context_switch",
		"title": "Supplier list should beat prior customer-risk context",
		"conversation": ["show customer risk", "show me suppliers"],
		"expected_action": "execute_fresh_governed_query",
		"expected_target": {
			"business_domain": "supplier_master",
			"capability_id": "supplier_master_read",
		},
		"failure_classes": ["stale_context_leakage", "fresh_query_isolation"],
		"quality_rule": "A clear self-contained supplier request must not be blocked by previous customer-risk context.",
		"activation_level": "fresh_query_route",
	},
	{
		"case_id": "nbu_fc0_rank_2_current_artifact_answer",
		"title": "Rank 2 should resolve to visible row facts",
		"conversation": ["show customer risk", "explain rank 2"],
		"expected_action": "answer_from_current_artifact",
		"expected_target": {
			"target_reference": "rank_n",
			"rank": 2,
			"artifact_family": "current_ranked_or_list_artifact",
		},
		"failure_classes": ["row_reference_failure", "definition_fallback_instead_of_row_answer"],
		"quality_rule": "Rank references should answer from the visible row when the row and fields are present.",
		"activation_level": "current_artifact_answer",
	},
	{
		"case_id": "nbu_fc0_above_ar_table_previous_context",
		"title": "Explicit above-AR-table reference should not switch to supplier list",
		"conversation": [
			"show customer risk",
			"show me suppliers",
			"who is in second position in the above AR table?",
		],
		"expected_action": "answer_from_current_artifact",
		"expected_target": {
			"target_reference": "previous_artifact",
			"artifact_family": "accounts_receivable_or_customer_risk",
			"rank": 2,
		},
		"failure_classes": ["previous_artifact_resolution_failure", "wrong_latest_context_used"],
		"quality_rule": "Explicit artifact names such as AR table must select the compatible previous artifact, not the latest unrelated supplier list.",
		"activation_level": "context_graph",
	},
	{
		"case_id": "nbu_fc0_credit_limit_requery",
		"title": "Missing credit limit should plan governed requery if a source exists",
		"conversation": ["show customer risk", "do you know the credit limit of that customer?"],
		"expected_action": "execute_governed_requery",
		"expected_target": {
			"business_domain": "customer_credit",
			"requested_metrics": ["credit_limit"],
			"target_reference": "selected_entity_or_rank_n",
		},
		"failure_classes": ["missing_evidence_requery_gap", "selected_entity_carryover_gap"],
		"quality_rule": "When current evidence lacks a requested field, the assistant should requery an approved source when available.",
		"activation_level": "governed_requery_plan",
	},
	{
		"case_id": "nbu_fc0_customer_risk_correction",
		"title": "User correction should escape wrong customer-list context",
		"conversation": [
			"okay show me again your customer risky table",
			"I am not asking plain list, I am asking customer risky",
		],
		"expected_action": "execute_fresh_governed_query",
		"expected_target": {
			"business_domain": "customer_risk",
			"preferred_family_id": "customer_risk_as_of",
		},
		"failure_classes": ["correction_intent_failure", "stale_context_leakage"],
		"quality_rule": "A correction that names the intended business concept should reset stale context and reroute.",
		"activation_level": "fresh_query_route",
	},
	{
		"case_id": "nbu_fc0_ar_ap_health_composite",
		"title": "AR/AP health should select working-capital health surface",
		"conversation": ["evaluate company health based on AR/AP"],
		"expected_action": "execute_fresh_governed_query",
		"expected_target": {
			"business_domain": "working_capital",
			"required_concepts": ["accounts_receivable", "accounts_payable", "health"],
		},
		"failure_classes": ["multi_domain_understanding_gap", "wrong_family_selection"],
		"quality_rule": "Combined AR and AP health wording should use the composite health surface when available.",
		"activation_level": "fresh_query_route",
	},
	{
		"case_id": "nbu_fc0_ambiguous_this_customer_clarification",
		"title": "Ambiguous deictic customer reference should ask one useful clarification",
		"conversation": ["show customer risk", "why is this customer risky?"],
		"expected_action": "ask_clarification",
		"expected_target": {
			"target_reference": "unclear",
			"option_source": "current_visible_rows",
		},
		"failure_classes": ["ambiguous_reference_guess", "report_repeat_instead_of_clarification"],
		"quality_rule": "When multiple visible rows exist and no unique row is selected, ask which row/customer the user means.",
		"activation_level": "safe_presentation_clarification",
	},
]


REQUIRED_BASELINE_CASE_KEYS = {
	"case_id",
	"title",
	"conversation",
	"expected_action",
	"expected_target",
	"failure_classes",
	"quality_rule",
	"activation_level",
}


def list_nbu_front_controller_baseline_cases() -> List[Dict[str, Any]]:
	return [dict(case) for case in NBU_FRONT_CONTROLLER_BASELINE_CASES]


def validate_nbu_front_controller_baseline_cases() -> Dict[str, Any]:
	errors: List[str] = []
	seen: set[str] = set()
	for index, case in enumerate(NBU_FRONT_CONTROLLER_BASELINE_CASES):
		missing = sorted(REQUIRED_BASELINE_CASE_KEYS.difference(case.keys()))
		case_id = str(case.get("case_id") or "").strip()
		if not case_id:
			errors.append(f"case_{index}:missing_case_id")
		elif case_id in seen:
			errors.append(f"{case_id}:duplicate_case_id")
		seen.add(case_id)
		for key in missing:
			errors.append(f"{case_id or 'case_' + str(index)}:missing_{key}")
		if not isinstance(case.get("conversation"), list) or not case.get("conversation"):
			errors.append(f"{case_id}:conversation_must_be_non_empty_list")
		if not isinstance(case.get("expected_target"), dict) or not case.get("expected_target"):
			errors.append(f"{case_id}:expected_target_must_be_non_empty_dict")
		if not isinstance(case.get("failure_classes"), list) or not case.get("failure_classes"):
			errors.append(f"{case_id}:failure_classes_must_be_non_empty_list")
	return {
		"ok": not errors,
		"schema_version": NBU_FRONT_CONTROLLER_CASE_SCHEMA_VERSION,
		"case_count": len(NBU_FRONT_CONTROLLER_BASELINE_CASES),
		"errors": errors,
	}
