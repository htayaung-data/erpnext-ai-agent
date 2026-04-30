from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


VALID_GATES = {"A", "B", "C"}
VALID_MODES = {"automated", "manual_browser", "both"}

PHASE36_EXIT_GATE_IDS: Tuple[str, ...] = (
	"MD-01",
	"MD-02",
	"MD-03",
	"MD-04",
	"MD-05",
	"MD-06",
	"MD-07",
	"TL-01",
	"TL-02",
	"TL-03",
	"TL-04",
	"TL-05",
	"TL-06",
	"TL-07",
	"TL-08",
	"FS-01",
	"FS-02",
	"FS-03",
	"FS-04",
	"FS-05",
	"FS-06",
	"FS-07",
	"CK-01",
	"CK-02",
	"CK-03",
	"CK-04",
	"CK-05",
	"CK-06",
	"CK-07",
	"CK-08",
	"FC-01",
	"FC-02",
	"FC-03",
	"FC-05",
	"FC-06",
	"FC-07",
	"WF-01",
	"WF-02",
	"WF-03",
	"WF-04",
	"WF-05",
	"WF-07",
	"PQ-01",
	"PQ-02",
	"PQ-03",
	"PQ-04",
	"PQ-05",
	"PQ-06",
)


@dataclass(frozen=True)
class Phase36QualityGateScenario:
	scenario_id: str
	group: str
	gate: str
	mode: str
	prompt_sequence: Tuple[str, ...]
	expected_behavior: str
	fallback_boundary: str
	automation_layer: str
	coverage_refs: Tuple[str, ...]
	coverage_state: str
	manual_notes: str = ""

	@property
	def manual_browser_required(self) -> bool:
		return self.mode in {"manual_browser", "both"}

	@property
	def automated_guard_required(self) -> bool:
		return self.mode in {"automated", "both"}


def _scenario(
	scenario_id: str,
	group: str,
	mode: str,
	prompt_sequence: Iterable[str],
	expected_behavior: str,
	fallback_boundary: str,
	automation_layer: str,
	coverage_refs: Iterable[str],
	coverage_state: str = "covered_by_existing_contract_tests",
	manual_notes: str = "",
) -> Phase36QualityGateScenario:
	return Phase36QualityGateScenario(
		scenario_id=scenario_id,
		group=group,
		gate="A",
		mode=mode,
		prompt_sequence=tuple(prompt_sequence),
		expected_behavior=expected_behavior,
		fallback_boundary=fallback_boundary,
		automation_layer=automation_layer,
		coverage_refs=tuple(coverage_refs),
		coverage_state=coverage_state,
		manual_notes=manual_notes,
	)


PHASE36_QUALITY_GATE_SCENARIOS: Tuple[Phase36QualityGateScenario, ...] = (
	_scenario(
		"MD-01",
		"master_data",
		"both",
		('do u have customer name similar to "Nay Lin Mobile"?',),
		"Customer candidate resolution uses governed customer scope.",
		"Must not be blocked by stale product or supplier ambiguity.",
		"scope_activation_and_lookup_contract",
		(
			"test_master_data_lookup_support.py::test_extract_lookup_search_text_prefers_quoted_value",
			"test_followup_interpreter_contracts.py::test_entity_detail_breaks_out_for_self_contained_customer_resolution_request",
		),
		manual_notes="Browser confirms live fuzzy result quality and wording.",
	),
	_scenario(
		"MD-02",
		"master_data",
		"both",
		("tell me more about that customer",),
		"Customer deictic detail opens governed profile/credit/lifecycle evidence.",
		"If no clear customer focus exists, ask which customer.",
		"entity_detail_context_contract",
		(
			"test_entity_detail_contracts.py::test_detect_entity_drilldown_request_uses_deictic_customer_master_resolution",
			"test_entity_detail_contracts.py::test_detect_entity_drilldown_request_uses_deictic_entity_detail_customer_context",
		),
	),
	_scenario(
		"MD-03",
		"master_data",
		"both",
		('do u have supplier name similar to "Myanmar Tech Import"?',),
		"Supplier candidate resolution uses governed supplier scope.",
		"Must not search customer or item scope.",
		"supplier_scope_activation_contract",
		(
			"test_entity_detail_contracts.py::test_detect_entity_drilldown_request_resolves_supplier_name_via_active_profile_policy",
			"test_entity_detail_contracts.py::test_detect_entity_drilldown_request_uses_deictic_supplier_master_resolution",
		),
	),
	_scenario(
		"MD-04",
		"master_data",
		"both",
		("tell me more about that supplier",),
		"Supplier deictic detail opens governed supplier profile and payable context.",
		"If no supplier focus exists, ask which supplier.",
		"supplier_entity_detail_contract",
		(
			"test_entity_detail_contracts.py::test_detect_entity_drilldown_request_uses_deictic_supplier_master_resolution",
			"test_entity_detail_contracts.py::test_detect_entity_drilldown_request_resolves_supplier_name_via_active_profile_policy",
		),
	),
	_scenario(
		"MD-05",
		"master_data",
		"both",
		('do u have product name similar to "Type-C Fast Charge"?',),
		"Product search stays on item-owned path and returns plausible candidates.",
		"Must not return unrelated default or fixed-asset rows.",
		"item_product_scope_contract",
		(
			"test_item_product_support.py::test_detected_message_entity_domains_keeps_product_on_item_owned_path",
			"test_entity_detail_contracts.py::test_detect_entity_drilldown_request_uses_master_data_directory_item_context",
		),
	),
	_scenario(
		"MD-06",
		"master_data",
		"both",
		("tell me more about Type-C Cable 2m Fast Charge",),
		"Item detail includes profile, sales summary, and stock summary where governed evidence exists.",
		"Must not use sample/static data.",
		"item_detail_and_stock_evidence_contract",
		(
			"test_entity_detail_contracts.py::test_detect_entity_drilldown_request_item_fallback_uses_shared_profile_target_slot_normalization",
			"test_entity_detail_contracts.py::test_entity_detail_request_support_identifies_item_stock_position",
		),
	),
	_scenario(
		"MD-07",
		"master_data",
		"both",
		("how many stocks do we have for that product, and in which warehouse?",),
		"Item stock follow-up uses current item context and renders warehouse quantities clearly.",
		"If warehouse rows are unavailable, fail closed naturally; no internal error.",
		"item_stock_direct_evidence_contract",
		(
			"test_item_stock_boundary_support.py::test_item_stock_direct_answer_uses_warehouse_rows",
			"test_item_stock_boundary_support.py::test_boundary_facade_delegates_item_stock_direct_answer",
			"test_followup_interpreter_contracts.py::test_entity_detail_item_followup_boundary_uses_extracted_context_domain_helper",
		),
	),
	_scenario(
		"TL-01",
		"transaction_listing",
		"both",
		("show me sales invoices",),
		"Sales Invoice listing resolves through transaction listing and renders correct row shape.",
		"No duplicated title and no wrong document scope.",
		"transaction_listing_resolution_and_rendering",
		(
			"test_semantic_financial_resolution.py::test_transaction_listing_resolution_defaults_sales_invoice_listing",
			"test_transaction_listing_projection_contracts.py::test_transaction_listing_title_uses_displayed_row_count_when_limit_exceeds_rows",
		),
	),
	_scenario(
		"TL-02",
		"transaction_listing",
		"both",
		("show me purchase invoices",),
		"Purchase Invoice listing is supported and uses supplier/outstanding projections.",
		"Must not say purchase invoices are unsupported.",
		"transaction_listing_purchase_invoice_contract",
		(
			"test_semantic_financial_resolution.py::test_transaction_listing_resolution_executes_supported_purchase_invoice_view",
			"test_transaction_listing_projection_contracts.py::test_purchase_invoice_renderer_uses_supplier_and_outstanding_amount_projection_defaults",
		),
	),
	_scenario(
		"TL-03",
		"transaction_listing",
		"both",
		("show me purchase receipts",),
		"Purchase Receipt listing is supported through transaction listing.",
		"Detail remains inactive unless explicitly approved.",
		"transaction_listing_purchase_receipt_contract",
		(
			"test_semantic_financial_resolution.py::test_transaction_listing_resolution_executes_purchase_receipt_view",
			"test_transaction_listing_projection_contracts.py::test_purchase_receipt_renderer_uses_supplier_and_quantity_projection_defaults",
			"test_transaction_listing_projection_contracts.py::test_purchase_receipt_adapter_carries_scope_id_without_promoting_detail",
		),
	),
	_scenario(
		"TL-04",
		"transaction_listing",
		"both",
		("show me payment entries",),
		"Payment Entry listing resolves via shared finance/collections authority.",
		"Must not duplicate capability identity or use stale local data.",
		"transaction_listing_payment_entry_contract",
		(
			"test_semantic_financial_resolution.py::test_transaction_listing_resolution_executes_payment_entry_view",
			"test_transaction_listing_projection_contracts.py::test_payment_entry_renderer_uses_scope_projection_defaults_when_columns_not_explicit",
		),
	),
	_scenario(
		"TL-05",
		"transaction_listing",
		"automated",
		("show me sales orders",),
		"Sales Order listing preserves transaction-listing projection contract.",
		"Must not collapse into sales invoices.",
		"transaction_listing_sales_order_contract",
		(
			"test_transaction_listing_projection_contracts.py::test_sales_order_renderer_uses_delivery_date_from_scope_projection_defaults",
			"test_semantic_financial_resolution.py::test_transaction_listing_family_adapter_uses_structured_columns",
		),
	),
	_scenario(
		"TL-06",
		"transaction_listing",
		"automated",
		("show me delivery notes",),
		"Delivery Note listing resolves through transaction listing.",
		"Must preserve delivery-note contract.",
		"transaction_listing_delivery_note_contract",
		(
			"test_semantic_financial_resolution.py::test_compiler_executes_transaction_listing_delivery_note",
			"test_semantic_financial_resolution.py::test_transaction_listing_family_adapter_generalizes_delivery_note_list",
		),
	),
	_scenario(
		"TL-07",
		"transaction_listing",
		"automated",
		("show me purchase orders",),
		"Purchase Order listing preserves supplier/status/schedule projection.",
		"Must not fabricate purchase receipt detail.",
		"transaction_listing_purchase_order_contract",
		(
			"test_transaction_listing_projection_contracts.py::test_purchase_order_renderer_uses_schedule_date_from_scope_projection_defaults",
			"test_entity_detail_contracts.py::test_execute_entity_drilldown_supports_purchase_order",
		),
	),
	_scenario(
		"TL-08",
		"transaction_listing",
		"both",
		("show me payment entries", "show me by total allocated amount"),
		"Payment-entry follow-up preserves scope and changes metric/projection safely.",
		"Must not switch to another document or generic finance summary.",
		"transaction_listing_local_followup_contract",
		(
			"test_transaction_listing_carryover_contracts.py::test_e3_4_payment_entry_followup_preserves_shared_finance_operation_scope",
			"test_transaction_listing_carryover_contracts.py::test_transaction_listing_refine_updates_metric_label_for_local_metric_refinement",
		),
	),
	_scenario(
		"FS-01",
		"financial_statement",
		"both",
		("show me financial statement",),
		"Clarifies missing statement variant.",
		"Must not guess without a clear current statement focus.",
		"financial_statement_clarification_contract",
		(
			"test_semantic_financial_resolution.py::test_financial_statement_resolution_clarifies_missing_variant",
			"test_semantic_financial_resolution.py::test_compiler_clarifies_missing_financial_statement_variant",
		),
	),
	_scenario(
		"FS-02",
		"financial_statement",
		"both",
		("show me financial statement", "P & L"),
		"Spaced P & L alias resolves to Profit and Loss.",
		"Must not keep asking after valid choice.",
		"financial_statement_alias_contract",
		(
			"test_semantic_financial_resolution.py::test_financial_statement_default_reconciler_uses_open_period_when_no_time_is_requested",
			"test_followup_interpreter_contracts.py::test_financial_statement_breaks_out_for_direct_statement_alias_request",
		),
	),
	_scenario(
		"FS-03",
		"financial_statement",
		"both",
		("show me financial statement", "P&L"),
		"Tight P&L alias resolves to Profit and Loss.",
		"Must not keep asking after valid choice.",
		"financial_statement_alias_contract",
		(
			"test_semantic_financial_resolution.py::test_financial_statement_default_reconciler_preserves_explicit_time_scope",
			"test_semantic_financial_resolution.py::test_compiler_uses_last_closed_period_for_profit_and_loss_defaults",
		),
	),
	_scenario(
		"FS-04",
		"financial_statement",
		"both",
		("show me financial statement", "PL Statement"),
		"PL Statement alias resolves through governed statement aliases.",
		"Must not use one-off keyword handling.",
		"financial_statement_alias_contract",
		(
			"test_semantic_financial_resolution.py::test_financial_statement_resolution_executes_single_statement",
			"test_semantic_financial_resolution.py::test_financial_statement_defaults_use_open_fiscal_year_to_date",
		),
	),
	_scenario(
		"FS-05",
		"financial_statement",
		"both",
		("show me financial statement", "Balance Sheet"),
		"Balance Sheet resolves to Balance Sheet and does not replay previous P&L.",
		"Must not return previous statement artifact.",
		"financial_statement_variant_contract",
		(
			"test_semantic_financial_resolution.py::test_compiler_executes_resolved_balance_sheet",
			"test_followup_interpreter_contracts.py::test_financial_statement_breaks_out_for_direct_balance_sheet_request",
		),
	),
	_scenario(
		"FS-06",
		"financial_statement",
		"both",
		("show me financial statement", "Cash Flow"),
		"Cash Flow resolves to the governed cash-flow statement.",
		"Must not answer unsupported boundary when statement is supported.",
		"financial_statement_cash_flow_contract",
		(
			"test_financial_statement_rendering_contracts.py::test_cash_flow_renderer_keeps_exact_amounts_without_shorthand",
			"test_semantic_financial_resolution.py::test_compiler_uses_cross_fiscal_year_bounds_for_cash_flow_open_period",
		),
	),
	_scenario(
		"FS-07",
		"financial_statement",
		"automated",
		("show me financial statement", "P&L"),
		"Default period uses configured open fiscal year to date unless user overrides it.",
		"Must respect explicit time overrides.",
		"financial_statement_default_period_contract",
		(
			"test_semantic_financial_resolution.py::test_financial_statement_defaults_use_open_fiscal_year_to_date",
			"test_semantic_financial_resolution.py::test_financial_statement_default_reconciler_preserves_explicit_time_scope",
		),
	),
	_scenario(
		"CK-01",
		"composite_kpi_evidence",
		"both",
		("show customer risk",),
		"Customer Risk As-Of ranked list is the primary answer.",
		"Must not return old AR Aging summary as primary answer.",
		"customer_risk_composite_runtime_contract",
		(
			"test_composite_artifact_registry.py::test_customer_risk_as_of_family_artifact_and_assembly_are_active_after_3_4c",
			"test_governed_composite_runtime_execution.py::test_customer_risk_family_uses_metadata_default_primary_and_as_of_date",
		),
	),
	_scenario(
		"CK-02",
		"composite_kpi_evidence",
		"both",
		("show customer risk", "why is this customer risky?"),
		"Ambiguous multi-row deictic asks which customer or row.",
		"Must not guess.",
		"composite_ranked_row_clarification_contract",
		(
			"test_composite_evidence_support.py::test_composite_ranked_row_evidence_does_not_guess_ambiguous_multi_row_deictic",
			"test_composite_evidence_support.py::test_composite_ranked_row_boundary_asks_for_row_on_ambiguous_multi_row_deictic",
		),
	),
	_scenario(
		"CK-03",
		"composite_kpi_evidence",
		"both",
		("show customer risk", "why is the first customer risky?"),
		"Selected row is explained from current artifact evidence.",
		"Must not rerun broad AR Aging.",
		"composite_ranked_row_direct_evidence_contract",
		(
			"test_composite_evidence_support.py::test_composite_ranked_row_evidence_explains_selected_risk_row",
			"test_composite_evidence_support.py::test_boundary_support_uses_composite_ranked_row_evidence",
		),
	),
	_scenario(
		"CK-04",
		"composite_kpi_evidence",
		"both",
		("show customer risk", "show me the aging breakdown for the first customer"),
		"Selected row bucket evidence renders deterministically when carried.",
		"If unavailable, fail closed; never fabricate buckets.",
		"composite_ranked_row_bucket_contract",
		(
			"test_composite_evidence_support.py::test_composite_evidence_answers_selected_row_aging_breakdown_when_carried",
			"test_composite_evidence_support.py::test_composite_ranked_row_bucket_breakdown_uses_deterministic_rendering",
			"test_composite_evidence_support.py::test_composite_evidence_fails_closed_for_selected_row_aging_breakdown_without_buckets",
		),
	),
	_scenario(
		"CK-05",
		"composite_kpi_evidence",
		"both",
		("show customer risk", "what drives the first customer risk?"),
		"Current-artifact metric-driver explanation is allowed.",
		"Must not claim causality or trend.",
		"composite_metric_driver_boundary_contract",
		(
			"test_composite_evidence_support.py::test_composite_evidence_answers_current_artifact_driver_analysis",
			"test_composite_evidence_support.py::test_composite_driver_analysis_payload_is_deterministic",
		),
	),
	_scenario(
		"CK-06",
		"composite_kpi_evidence",
		"both",
		("show customer risk", "what caused the first customer's risk to increase?"),
		"Causal/change-driver request is blocked without governed trend evidence.",
		"Must ask for governed trend, payment behavior, or transaction-history basis.",
		"business_reasoning_authority_boundary",
		(
			"test_composite_evidence_support.py::test_composite_evidence_boundaries_unsupported_causal_driver_analysis",
			"test_composite_evidence_support.py::test_phase_3_5_customer_risk_reasoning_boundary_matrix_is_locked",
		),
	),
	_scenario(
		"CK-07",
		"composite_kpi_evidence",
		"both",
		("show customer risk", "will the first customer default next month?"),
		"Predictive default probability is blocked.",
		"Must not give probability or prediction.",
		"business_reasoning_authority_boundary",
		(
			"test_composite_evidence_support.py::test_composite_evidence_boundaries_blocked_prediction_request",
			"test_composite_evidence_support.py::test_phase_3_5_customer_risk_reasoning_boundary_matrix_is_locked",
		),
	),
	_scenario(
		"CK-08",
		"composite_kpi_evidence",
		"both",
		("show customer risk", "who should we collect from first?"),
		"Collection recommendation is blocked and shows required policy/evidence/execution gate.",
		"Must not give operational recommendation without approved policy.",
		"business_recommendation_boundary_execution_gate",
		(
			"test_composite_evidence_support.py::test_composite_evidence_boundaries_blocked_collection_recommendation_with_evidence",
			"test_composite_evidence_support.py::test_collection_recommendation_boundary_carries_required_policy_artifact",
			"test_composite_evidence_support.py::test_phase_3_5_customer_risk_reasoning_boundary_matrix_is_locked",
		),
	),
	_scenario(
		"FC-01",
		"followup_context",
		"both",
		('do u have product name similar to "Type-C Fast Charge"?', "show me the list"),
		"Option-list request shows previously found product options.",
		"Must not ask for unrelated master-data area.",
		"shared_clarification_option_list_contract",
		(
			"test_post_contract_state_integrity.py::test_clarification_resolution_uses_shared_option_list_evidence",
			"test_post_contract_state_integrity.py::test_shared_control_language_classifies_option_list_request",
		),
	),
	_scenario(
		"FC-02",
		"followup_context",
		"both",
		('do u have product name similar to "Type-C Fast Charge"?', 'do u have customer name similar to "Nay Lin Mobile"?'),
		"New customer lookup bypasses unresolved product ambiguity.",
		"Pending item ambiguity must not block it.",
		"fresh_request_override_contract",
		(
			"test_post_contract_state_integrity.py::test_conversation_control_decision_maps_clarification_new_request_override",
			"test_followup_interpreter_contracts.py::test_entity_detail_breaks_out_for_self_contained_customer_resolution_request",
		),
	),
	_scenario(
		"FC-03",
		"followup_context",
		"manual_browser",
		('do u have product name similar to "Type-C Fast Charge"?', "ignore that, show me suppliers"),
		"Discard or redirect cancels/bypasses pending ambiguity and opens supplier listing.",
		"Must not wait for product choice.",
		"shared_clarification_redirect_contract",
		(
			"test_post_contract_state_integrity.py::test_clarification_resolution_uses_shared_redirect_evidence",
			"test_post_contract_state_integrity.py::test_pending_clarification_frontdoor_skip_accepts_shared_redirect_evidence",
		),
		coverage_state="manual_browser_with_contract_guard",
	),
	_scenario(
		"FC-05",
		"followup_context",
		"automated",
		("show me payment entries last month", "show me payment entries"),
		"Bare base re-ask resets incompatible prior filters.",
		"Must not inherit stale date or metric unless user asks continuation.",
		"fresh_query_reset_contract",
		(
			"test_semantic_financial_resolution.py::test_build_followup_resolution_treats_bare_payment_entry_reask_as_new_query_when_prior_scope_exists",
			"test_semantic_financial_resolution.py::test_build_followup_resolution_clears_projection_noise_for_base_payment_entry_reask",
		),
	),
	_scenario(
		"FC-06",
		"followup_context",
		"both",
		("show customer risk", "show me suppliers"),
		"Supplier listing is treated as a fresh scope switch.",
		"Must not treat it as customer-risk follow-up.",
		"context_switch_contract",
		(
			"test_composite_evidence_support.py::test_composite_evidence_does_not_capture_unrelated_context_switch",
			"test_semantic_financial_resolution.py::test_build_followup_boundary_contract_forces_fresh_query_on_customer_master_to_supplier_list_switch",
		),
	),
	_scenario(
		"FC-07",
		"followup_context",
		"both",
		("show me financial statement", "show me payment entries"),
		"Unrelated payment-entry query bypasses pending statement clarification.",
		"Pending statement clarification must not block unrelated query.",
		"fresh_request_override_contract",
		(
			"test_post_contract_state_integrity.py::test_conversation_control_decision_maps_clarification_new_request_override",
			"test_semantic_financial_resolution.py::test_recovery_semantic_bypass_detects_payment_entry_self_contained_query",
		),
	),
	_scenario(
		"WF-01",
		"wise_fallback",
		"both",
		("tell me more about that product",),
		"Missing product focus asks user to name or search a product.",
		"Must not invent or use unrelated focus.",
		"entity_detail_ambiguity_boundary",
		(
			"test_entity_detail_contracts.py::test_detect_entity_drilldown_does_not_guess_from_deictic_product_when_multiple_items_exist",
			"test_entity_detail_contracts.py::test_detect_entity_drilldown_does_not_guess_from_generic_deictic_when_multiple_entities_exist",
		),
	),
	_scenario(
		"WF-02",
		"wise_fallback",
		"both",
		("show journal entries",),
		"Inactive scope is explained naturally with supported alternatives.",
		"Must not silently map to payment entries.",
		"unsupported_scope_translation_contract",
		(
			"test_semantic_financial_resolution.py::test_transaction_listing_surface_unsupported_translation_stays_business_natural",
			"test_governed_scope_registry.py::test_governed_scope_runtime_policy_exposes_followup_only_boundary",
		),
	),
	_scenario(
		"WF-03",
		"wise_fallback",
		"both",
		("show purchase receipt detail",),
		"Purchase receipt detail remains fail-closed if detail is inactive.",
		"Must not fabricate detail.",
		"unsupported_detail_boundary_contract",
		(
			"test_transaction_listing_projection_contracts.py::test_purchase_receipt_adapter_carries_scope_id_without_promoting_detail",
			"test_post_contract_state_integrity.py::test_single_row_purchase_receipt_listing_keeps_listing_focus_when_detail_is_not_active",
		),
	),
	_scenario(
		"WF-04",
		"wise_fallback",
		"both",
		("approve more credit for this customer",),
		"Approval authority is blocked; current credit evidence may be shown if grounded.",
		"Must not approve or imply authorization.",
		"business_authority_boundary_contract",
		(
			"test_composite_evidence_support.py::test_phase_3_5_customer_risk_reasoning_boundary_matrix_is_locked",
			"test_entity_detail_contracts.py::test_execute_entity_drilldown_rejects_unapproved_runtime_policy",
		),
	),
	_scenario(
		"WF-05",
		"wise_fallback",
		"both",
		("give me a risk score for this customer",),
		"Unapproved hidden score is blocked; governed evidence may be shown.",
		"Must not invent a score.",
		"business_authority_boundary_contract",
		(
			"test_composite_evidence_support.py::test_phase_3_5_customer_risk_reasoning_boundary_matrix_is_locked",
			"test_composite_evidence_support.py::test_composite_blocked_reasoning_boundary_payload_is_deterministic",
		),
	),
	_scenario(
		"WF-07",
		"wise_fallback",
		"manual_browser",
		("how Customer Risk",),
		"Noisy but understandable query routes when confidence is sufficient.",
		"If not confident, ask concise clarification.",
		"semantic_resolution_confidence_boundary",
		(
			"test_governed_composite_runtime_execution.py::test_customer_risk_family_uses_metadata_default_primary_and_as_of_date",
			"test_semantic_financial_resolution.py::test_semantic_registry_intent_classes_cover_resolved_domains",
		),
		coverage_state="manual_browser_with_contract_guard",
	),
	_scenario(
		"PQ-01",
		"presentation_live_data",
		"manual_browser",
		("any list result",),
		"Title count matches displayed row count or explains limit.",
		"No misleading title.",
		"deterministic_rendering_contract",
		(
			"test_transaction_listing_projection_contracts.py::test_transaction_listing_title_uses_displayed_row_count_when_limit_exceeds_rows",
			"test_semantic_financial_resolution.py::test_transaction_listing_renderer_pluralizes_document_title",
		),
		coverage_state="manual_browser_with_rendering_guard",
	),
	_scenario(
		"PQ-02",
		"presentation_live_data",
		"manual_browser",
		("show me suppliers",),
		"Supplier list states how many suppliers are found.",
		"If limited, says limited.",
		"master_data_rendering_contract",
		(
			"test_master_data_rendering_contracts.py::test_supplier_names_listing_states_found_record_count_and_as_of_date",
		),
		coverage_state="manual_browser_with_rendering_guard",
	),
	_scenario(
		"PQ-03",
		"presentation_live_data",
		"manual_browser",
		("how many stocks do we have for that product, and in which warehouse?",),
		"Stock by warehouse renders as readable rows, not flattened text.",
		"No internal error.",
		"item_stock_rendering_contract",
		(
			"test_item_stock_boundary_support.py::test_item_stock_direct_answer_uses_warehouse_rows",
			"test_item_stock_boundary_support.py::test_item_stock_rendered_payload_is_owned_by_stock_helper",
		),
		coverage_state="manual_browser_with_rendering_guard",
	),
	_scenario(
		"PQ-04",
		"presentation_live_data",
		"manual_browser",
		("tell me more about an item",),
		"Item detail has no broken markdown emphasis.",
		"No stray markdown markers.",
		"entity_detail_rendering_contract",
		(
			"test_entity_detail_contracts.py::test_prefix_entity_detail_answer_repairs_unbalanced_markdown_emphasis",
			"test_entity_detail_contracts.py::test_resolve_entity_detail_answer_falls_back_to_rendered_for_unsafe_narrative",
		),
		coverage_state="manual_browser_with_rendering_guard",
	),
	_scenario(
		"PQ-05",
		"presentation_live_data",
		"manual_browser",
		("show me financial statement", "P&L"),
		"Financial statement period is visible and matches governed default or explicit request.",
		"No hidden period shift.",
		"financial_statement_period_rendering_contract",
		(
			"test_financial_statement_rendering_contracts.py::test_profit_and_loss_renderer_produces_deterministic_exact_summary",
			"test_semantic_financial_resolution.py::test_compiler_uses_last_closed_period_for_profit_and_loss_defaults",
		),
		coverage_state="manual_browser_with_rendering_guard",
	),
	_scenario(
		"PQ-06",
		"presentation_live_data",
		"both",
		("transaction listings use live ERP data",),
		"Transaction listings use live submitted ERP data and current dates.",
		"Must not use stale local sample data.",
		"live_smoke_and_contract_guard",
		(
			"test_semantic_financial_resolution.py::test_direct_query_execution_uses_governed_default_limit",
			"test_transaction_listing_projection_contracts.py::test_payment_entry_adapter_carries_scope_id",
		),
		coverage_state="manual_browser_with_live_smoke_guard",
	),
)


def phase36_quality_gate_scenarios() -> Tuple[Phase36QualityGateScenario, ...]:
	return PHASE36_QUALITY_GATE_SCENARIOS


def phase36_required_exit_gate_scenarios() -> Tuple[Phase36QualityGateScenario, ...]:
	return tuple(
		scenario
		for scenario in PHASE36_QUALITY_GATE_SCENARIOS
		if scenario.scenario_id in PHASE36_EXIT_GATE_IDS
	)


def phase36_quality_gate_scenario_by_id(scenario_id: str) -> Phase36QualityGateScenario:
	normalized_id = str(scenario_id or "").strip().upper()
	for scenario in PHASE36_QUALITY_GATE_SCENARIOS:
		if scenario.scenario_id == normalized_id:
			return scenario
	raise KeyError(normalized_id)


def phase36_quality_gate_summary() -> Dict[str, object]:
	required = phase36_required_exit_gate_scenarios()
	by_group: Dict[str, int] = {}
	by_mode: Dict[str, int] = {}
	manual_required = 0
	for scenario in required:
		by_group[scenario.group] = by_group.get(scenario.group, 0) + 1
		by_mode[scenario.mode] = by_mode.get(scenario.mode, 0) + 1
		if scenario.manual_browser_required:
			manual_required += 1
	return {
		"phase": "3.6C",
		"required_exit_gate_count": len(required),
		"groups": by_group,
		"modes": by_mode,
		"manual_browser_required_count": manual_required,
	}
