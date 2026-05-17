from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Iterable, List

from .natural_business_understanding_contracts import CONTRACT_VERSION
from .regression_suite_governance import BLOCKING_MANUAL, BLOCKING_RELEASE


REGRESSION_SCENARIO_PACK_CONTRACT_TYPE = "qwen_regression_scenario_pack_contract"
REGRESSION_SCENARIO_CONTRACT_TYPE = "qwen_regression_scenario_contract"

REGRESSION_SCENARIO_PACK_SUITE_ID = "s7_regression_scenario_packs"

EXECUTION_DETERMINISTIC_CONTRACT = "deterministic_contract"
EXECUTION_MANUAL_BROWSER_UAT = "manual_browser_uat"

PACK_VISIBLE_CONTEXT_SWITCHING = "visible_context_switching"
PACK_PROJECTION_AND_CARDINALITY = "projection_and_cardinality"
PACK_FINANCIAL_STATEMENT_DRILLDOWN = "financial_statement_drilldown"
PACK_POLICY_BOUNDARIES = "policy_boundaries"
PACK_TRACE_AND_MODEL_ROLE = "trace_and_model_role"
PACK_MANUAL_BROWSER_UAT = "manual_browser_uat"

REQUIRED_SCENARIO_PACK_IDS = [
	PACK_VISIBLE_CONTEXT_SWITCHING,
	PACK_PROJECTION_AND_CARDINALITY,
	PACK_FINANCIAL_STATEMENT_DRILLDOWN,
	PACK_POLICY_BOUNDARIES,
	PACK_TRACE_AND_MODEL_ROLE,
	PACK_MANUAL_BROWSER_UAT,
]

REQUIRED_SCENARIO_FIELDS = [
	"scenario_id",
	"family",
	"turns",
	"expected_route",
	"expected_artifact_family",
	"expected_entity_type",
	"expected_row_reference",
	"expected_authority_source",
	"expected_policy_boundary",
	"expected_model_role_lane",
	"expected_answer_mode",
	"manual_uat_prompt",
	"pass_criteria",
	"blocking_level",
]

COMMON_RELATED_CONTRACTS = [
	"context_frame_contract",
	"semantic_ownership_ledger",
	"final_answer_authority_contract",
	"policy_boundary_uniformity_contract",
	"requested_limit_cardinality_contract",
	"projection_preservation_contract",
	"model_role_observability_readiness_coverage",
	"regression_suite_boundary_contract",
]


S7_REGRESSION_SCENARIO_REGISTRY: List[Dict[str, Any]] = [
	{
		"scenario_id": "visible_ar_after_ap_typed_rank_2",
		"pack_id": PACK_VISIBLE_CONTEXT_SWITCHING,
		"family": "accounts_receivable_aging",
		"turns": [
			"Show top 7 customers by AR",
			"Show top 5 suppliers by AP",
			"Who is second in the above AR table?",
		],
		"expected_route": "visible_context_followup",
		"expected_artifact_family": "accounts_receivable_aging",
		"expected_entity_type": "customer",
		"expected_row_reference": "rank_2",
		"expected_authority_source": "visible_rendered_table",
		"expected_policy_boundary": "none",
		"expected_model_role_lane": "visible_context_followup:deterministic",
		"expected_answer_mode": "visible_context_answer",
		"manual_uat_prompt": "Run AR top 7, then AP top 5, then ask who is second in the above AR table.",
		"pass_criteria": [
			"Answer resolves to the rank 2 customer from the AR artifact, not the current AP artifact.",
			"Trace selected artifact family is accounts_receivable_aging and row reference is rank_2.",
		],
		"blocking_level": BLOCKING_RELEASE,
		"execution_mode": EXECUTION_DETERMINISTIC_CONTRACT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
	{
		"scenario_id": "visible_ap_current_rank_2",
		"pack_id": PACK_VISIBLE_CONTEXT_SWITCHING,
		"family": "accounts_payable_aging",
		"turns": ["Show top 5 suppliers by AP", "Who is second in the above table?"],
		"expected_route": "visible_context_followup",
		"expected_artifact_family": "accounts_payable_aging",
		"expected_entity_type": "supplier",
		"expected_row_reference": "rank_2",
		"expected_authority_source": "visible_rendered_table",
		"expected_policy_boundary": "none",
		"expected_model_role_lane": "visible_context_followup:deterministic",
		"expected_answer_mode": "visible_context_answer",
		"manual_uat_prompt": "Run AP top 5 suppliers, then ask who is second in the above table.",
		"pass_criteria": [
			"Answer resolves to the rank 2 supplier from the current AP artifact.",
			"Trace rejects stale non-current frames as lower-authority candidates.",
		],
		"blocking_level": BLOCKING_RELEASE,
		"execution_mode": EXECUTION_DETERMINISTIC_CONTRACT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
	{
		"scenario_id": "product_rank_2_after_million_projection",
		"pack_id": PACK_PROJECTION_AND_CARDINALITY,
		"family": "product_revenue_ranking",
		"turns": [
			"Top 7 products by revenue last month",
			"Display the values in millions",
			"Who is second in the above table?",
		],
		"expected_route": "visible_context_followup",
		"expected_artifact_family": "product_revenue_ranking",
		"expected_entity_type": "item",
		"expected_row_reference": "rank_2",
		"expected_authority_source": "visible_rendered_table",
		"expected_policy_boundary": "none",
		"expected_model_role_lane": "visible_context_followup:deterministic",
		"expected_answer_mode": "visible_context_answer",
		"manual_uat_prompt": "Run product top 7 revenue, show in millions, then ask who is second.",
		"pass_criteria": [
			"Answer preserves the projected revenue metric and selects rank 2 item.",
			"Trace selected entity type is item and row reference is rank_2.",
		],
		"blocking_level": BLOCKING_RELEASE,
		"execution_mode": EXECUTION_DETERMINISTIC_CONTRACT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
	{
		"scenario_id": "product_projection_qty_preserves_revenue",
		"pack_id": PACK_PROJECTION_AND_CARDINALITY,
		"family": "product_revenue_ranking",
		"turns": ["Top 7 products by revenue last year", "Include quantities alongside the results."],
		"expected_route": "projection_followup",
		"expected_artifact_family": "product_revenue_ranking",
		"expected_entity_type": "item",
		"expected_row_reference": "all_visible_rows",
		"expected_authority_source": "governed_erp_report_or_visible_projection",
		"expected_policy_boundary": "none",
		"expected_model_role_lane": "projection_contract:deterministic_or_light_semantic",
		"expected_answer_mode": "projection_preservation_answer",
		"manual_uat_prompt": "Run product top 7 revenue, then ask to include quantities alongside the results.",
		"pass_criteria": [
			"Output keeps Revenue and adds Quantity instead of replacing the original metric.",
			"Visible row count remains the requested top 7 unless the user changes it.",
		],
		"blocking_level": BLOCKING_RELEASE,
		"execution_mode": EXECUTION_DETERMINISTIC_CONTRACT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
	{
		"scenario_id": "product_top7_rank_8_out_of_range",
		"pack_id": PACK_PROJECTION_AND_CARDINALITY,
		"family": "product_revenue_ranking",
		"turns": ["Top 7 products by revenue last year", "Tell me more about rank 8 product."],
		"expected_route": "visible_context_followup",
		"expected_artifact_family": "product_revenue_ranking",
		"expected_entity_type": "item",
		"expected_row_reference": "none",
		"expected_authority_source": "visible_rendered_table",
		"expected_policy_boundary": "visible_context_out_of_range",
		"expected_model_role_lane": "visible_context_followup:deterministic",
		"expected_answer_mode": "visible_context_out_of_range",
		"manual_uat_prompt": "Run product top 7 revenue, then ask for rank 8 product details.",
		"pass_criteria": [
			"Answer refuses safely because only 7 visible rows exist.",
			"Trace status is out_of_range or bounded with row reference none.",
		],
		"blocking_level": BLOCKING_RELEASE,
		"execution_mode": EXECUTION_DETERMINISTIC_CONTRACT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
	{
		"scenario_id": "pl_cogs_source_document_rank_2",
		"pack_id": PACK_FINANCIAL_STATEMENT_DRILLDOWN,
		"family": "profit_and_loss_cogs_detail",
		"turns": ["Give me Profit and Loss", "Tell me more about COGS", "Who is second in the above table?"],
		"expected_route": "visible_context_followup",
		"expected_artifact_family": "profit_and_loss_cogs_detail",
		"expected_entity_type": "document",
		"expected_row_reference": "rank_2",
		"expected_authority_source": "visible_rendered_table",
		"expected_policy_boundary": "none",
		"expected_model_role_lane": "visible_context_followup:deterministic",
		"expected_answer_mode": "visible_context_answer",
		"manual_uat_prompt": "Run Profit and Loss, ask for COGS detail, then ask who is second in the above table.",
		"pass_criteria": [
			"Answer selects rank 2 source document from the COGS detail table.",
			"Trace selected entity type is document and authority source is visible_rendered_table.",
		],
		"blocking_level": BLOCKING_RELEASE,
		"execution_mode": EXECUTION_DETERMINISTIC_CONTRACT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
	{
		"scenario_id": "ar_rank_2_default_prediction_boundary",
		"pack_id": PACK_POLICY_BOUNDARIES,
		"family": "accounts_receivable_aging",
		"turns": [
			"Show top 5 customers by AR",
			"Who is rank 2 in the above table?",
			"Will this customer default next month?",
		],
		"expected_route": "visible_context_followup",
		"expected_artifact_family": "accounts_receivable_aging",
		"expected_entity_type": "customer",
		"expected_row_reference": "rank_2",
		"expected_authority_source": "visible_rendered_table",
		"expected_policy_boundary": "prediction_boundary",
		"expected_model_role_lane": "visible_context_followup:deterministic",
		"expected_answer_mode": "visible_context_boundary",
		"manual_uat_prompt": "Select rank 2 customer from AR, then ask if this customer will default next month.",
		"pass_criteria": [
			"Answer gives current visible facts but does not forecast a future payment outcome.",
			"Trace policy boundary is prediction_boundary.",
		],
		"blocking_level": BLOCKING_RELEASE,
		"execution_mode": EXECUTION_DETERMINISTIC_CONTRACT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
	{
		"scenario_id": "ar_first_customer_cause_boundary",
		"pack_id": PACK_POLICY_BOUNDARIES,
		"family": "accounts_receivable_aging",
		"turns": [
			"Show top 5 customers by AR",
			"From above table, what caused the first customer risk to increase?",
		],
		"expected_route": "visible_context_followup",
		"expected_artifact_family": "accounts_receivable_aging",
		"expected_entity_type": "customer",
		"expected_row_reference": "rank_1",
		"expected_authority_source": "visible_rendered_table",
		"expected_policy_boundary": "causal_boundary",
		"expected_model_role_lane": "visible_context_followup:deterministic",
		"expected_answer_mode": "visible_context_boundary",
		"manual_uat_prompt": "Run AR top 5, then ask what caused the first customer risk to increase.",
		"pass_criteria": [
			"Answer does not attribute cause from a point-in-time table.",
			"Trace policy boundary is causal_boundary and row reference is rank_1.",
		],
		"blocking_level": BLOCKING_RELEASE,
		"execution_mode": EXECUTION_DETERMINISTIC_CONTRACT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
	{
		"scenario_id": "ar_collection_recommendation_boundary",
		"pack_id": PACK_POLICY_BOUNDARIES,
		"family": "accounts_receivable_aging",
		"turns": ["Show top 5 customers by AR", "Which customer should we collect from first?"],
		"expected_route": "visible_context_followup",
		"expected_artifact_family": "accounts_receivable_aging",
		"expected_entity_type": "customer",
		"expected_row_reference": "rank_1",
		"expected_authority_source": "visible_rendered_table",
		"expected_policy_boundary": "recommendation_boundary",
		"expected_model_role_lane": "visible_context_followup:deterministic",
		"expected_answer_mode": "visible_context_boundary",
		"manual_uat_prompt": "Run AR top 5, then ask which customer should be collected from first.",
		"pass_criteria": [
			"Answer shows visible facts but does not recommend a collection action without approved policy.",
			"Trace policy boundary is recommendation_boundary.",
		],
		"blocking_level": BLOCKING_RELEASE,
		"execution_mode": EXECUTION_DETERMINISTIC_CONTRACT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
	{
		"scenario_id": "trace_inspection_model_role_coverage",
		"pack_id": PACK_TRACE_AND_MODEL_ROLE,
		"family": "visible_context_trace_inspection",
		"turns": ["Who is rank 2 in the above table?", "Show latest context authority trace"],
		"expected_route": "trace_inspection",
		"expected_artifact_family": "selected_visible_artifact",
		"expected_entity_type": "selected_visible_entity_type",
		"expected_row_reference": "selected_visible_row_reference",
		"expected_authority_source": "visible_rendered_table",
		"expected_policy_boundary": "none_or_selected_boundary",
		"expected_model_role_lane": "trace_inspection:deterministic",
		"expected_answer_mode": "visible_context_trace_inspection",
		"manual_uat_prompt": "After any visible-context answer, ask to show the latest context authority trace.",
		"pass_criteria": [
			"Trace output includes semantic ownership ledger, final answer authority, policy boundary, model-role observability, strict readiness, and coverage.",
			"Trace inspection payload exposes model-role coverage fields.",
		],
		"blocking_level": BLOCKING_RELEASE,
		"execution_mode": EXECUTION_DETERMINISTIC_CONTRACT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
	{
		"scenario_id": "requested_top5_top7_cardinality",
		"pack_id": PACK_PROJECTION_AND_CARDINALITY,
		"family": "accounts_receivable_aging",
		"turns": ["Show top 5 customers by AR", "Show top 7 customers by AR"],
		"expected_route": "fresh_query_and_visible_artifact_capture",
		"expected_artifact_family": "accounts_receivable_aging",
		"expected_entity_type": "customer",
		"expected_row_reference": "all_visible_rows",
		"expected_authority_source": "governed_erp_report",
		"expected_policy_boundary": "none",
		"expected_model_role_lane": "fresh_query:light_semantic_and_deterministic_report",
		"expected_answer_mode": "governed_report_answer",
		"manual_uat_prompt": "Ask for top 5 customers by AR, then top 7 customers by AR.",
		"pass_criteria": [
			"Top 5 returns exactly 5 visible rows and top 7 returns exactly 7 visible rows.",
			"Follow-up trace exposes requested row limit matching the rendered result.",
		],
		"blocking_level": BLOCKING_RELEASE,
		"execution_mode": EXECUTION_DETERMINISTIC_CONTRACT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
	{
		"scenario_id": "browser_manual_end_to_end_uat",
		"pack_id": PACK_MANUAL_BROWSER_UAT,
		"family": "manual_browser_uat",
		"turns": [
			"Run the approved S7 browser prompt checklist after deterministic gates pass.",
			"Record any mismatch between rendered answer, trace, and model-role metadata.",
		],
		"expected_route": "manual_browser_uat",
		"expected_artifact_family": "cross_family_manual_uat",
		"expected_entity_type": "varies_by_scenario",
		"expected_row_reference": "varies_by_scenario",
		"expected_authority_source": "scenario_declared_authority",
		"expected_policy_boundary": "scenario_declared_boundary",
		"expected_model_role_lane": "scenario_declared_model_role_lane",
		"expected_answer_mode": "manual_acceptance",
		"manual_uat_prompt": "Use the generated scenario prompts in the browser/chat UI and compare answer plus trace fields against the scenario contract.",
		"pass_criteria": [
			"Browser-visible behavior matches deterministic scenario contracts.",
			"No manual signoff is accepted without trace evidence for authority, policy, and model role.",
		],
		"blocking_level": BLOCKING_MANUAL,
		"execution_mode": EXECUTION_MANUAL_BROWSER_UAT,
		"related_contracts": COMMON_RELATED_CONTRACTS,
	},
]


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_registry(registry: Iterable[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
	out: List[Dict[str, Any]] = []
	for raw_entry in registry or S7_REGRESSION_SCENARIO_REGISTRY:
		if isinstance(raw_entry, dict):
			out.append(dict(raw_entry))
	return out


def regression_scenario_missing_fields(entry: Dict[str, Any]) -> List[str]:
	missing: List[str] = []
	for field in REQUIRED_SCENARIO_FIELDS:
		value = entry.get(field)
		if field in {"turns", "pass_criteria"}:
			if not _clean_list(value):
				missing.append(field)
		elif field not in entry or not _clean_text(value):
			missing.append(field)
	return missing


def build_regression_scenario_contract(entry: Dict[str, Any]) -> Dict[str, Any]:
	clean_entry = dict(entry or {})
	missing_fields = regression_scenario_missing_fields(clean_entry)
	execution_mode = _clean_text(clean_entry.get("execution_mode")) or EXECUTION_DETERMINISTIC_CONTRACT
	blocking_level = _clean_text(clean_entry.get("blocking_level"))
	return {
		"type": REGRESSION_SCENARIO_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"scenario_id": _clean_text(clean_entry.get("scenario_id")),
		"pack_id": _clean_text(clean_entry.get("pack_id")),
		"family": _clean_text(clean_entry.get("family")),
		"turns": _clean_list(clean_entry.get("turns")),
		"expected_route": _clean_text(clean_entry.get("expected_route")),
		"expected_artifact_family": _clean_text(clean_entry.get("expected_artifact_family")),
		"expected_entity_type": _clean_text(clean_entry.get("expected_entity_type")),
		"expected_row_reference": _clean_text(clean_entry.get("expected_row_reference")),
		"expected_authority_source": _clean_text(clean_entry.get("expected_authority_source")),
		"expected_policy_boundary": _clean_text(clean_entry.get("expected_policy_boundary")),
		"expected_model_role_lane": _clean_text(clean_entry.get("expected_model_role_lane")),
		"expected_answer_mode": _clean_text(clean_entry.get("expected_answer_mode")),
		"manual_uat_prompt": _clean_text(clean_entry.get("manual_uat_prompt")),
		"pass_criteria": _clean_list(clean_entry.get("pass_criteria")),
		"blocking_level": blocking_level,
		"execution_mode": execution_mode,
		"related_contracts": _clean_list(clean_entry.get("related_contracts")),
		"missing_fields": missing_fields,
		"scenario_complete": not missing_fields,
		"deterministic": execution_mode == EXECUTION_DETERMINISTIC_CONTRACT,
		"manual_uat": execution_mode == EXECUTION_MANUAL_BROWSER_UAT,
		"release_blocking": blocking_level == BLOCKING_RELEASE,
	}


def build_regression_scenario_pack_contract(
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	contract_owner: str = "s7_regression_scenario_packs",
) -> Dict[str, Any]:
	scenarios = [build_regression_scenario_contract(entry) for entry in _clean_registry(registry)]
	scenario_ids = [_clean_text(entry.get("scenario_id")) for entry in scenarios if _clean_text(entry.get("scenario_id"))]
	duplicate_scenario_ids = sorted({scenario_id for scenario_id in scenario_ids if scenario_ids.count(scenario_id) > 1})
	pack_ids = sorted({_clean_text(entry.get("pack_id")) for entry in scenarios if _clean_text(entry.get("pack_id"))})
	incomplete_scenarios = [
		_clean_text(entry.get("scenario_id")) or "unknown"
		for entry in scenarios
		if not bool(entry.get("scenario_complete"))
	]
	manual_scenarios = [entry for entry in scenarios if bool(entry.get("manual_uat"))]
	deterministic_scenarios = [entry for entry in scenarios if bool(entry.get("deterministic"))]
	missing_pack_ids = [pack_id for pack_id in REQUIRED_SCENARIO_PACK_IDS if pack_id not in pack_ids]
	contract_complete = bool(
		scenarios
		and deterministic_scenarios
		and manual_scenarios
		and not duplicate_scenario_ids
		and not incomplete_scenarios
		and not missing_pack_ids
	)
	return {
		"type": REGRESSION_SCENARIO_PACK_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"linked_regression_suite_id": REGRESSION_SCENARIO_PACK_SUITE_ID,
		"contract_complete": contract_complete,
		"scenario_count": len(scenarios),
		"deterministic_scenario_count": len(deterministic_scenarios),
		"manual_uat_scenario_count": len(manual_scenarios),
		"pack_ids": pack_ids,
		"required_pack_ids": list(REQUIRED_SCENARIO_PACK_IDS),
		"missing_pack_ids": missing_pack_ids,
		"duplicate_scenario_ids": duplicate_scenario_ids,
		"incomplete_scenarios": incomplete_scenarios,
		"deterministic_scenario_ids": [_clean_text(entry.get("scenario_id")) for entry in deterministic_scenarios],
		"manual_uat_scenario_ids": [_clean_text(entry.get("scenario_id")) for entry in manual_scenarios],
		"scenarios": scenarios,
		"created_at": _utc_now(),
	}


def deterministic_regression_scenarios(
	registry: Iterable[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
	return [
		scenario
		for scenario in build_regression_scenario_pack_contract(registry=registry).get("scenarios", [])
		if bool(scenario.get("deterministic"))
	]


def manual_uat_regression_scenarios(
	registry: Iterable[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
	return [
		scenario
		for scenario in build_regression_scenario_pack_contract(registry=registry).get("scenarios", [])
		if bool(scenario.get("manual_uat"))
	]
