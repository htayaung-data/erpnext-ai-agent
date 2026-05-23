# EC-8-B Public Service Surface / Caller Audit

Decision target: `ec_8_b_public_service_surface_caller_audit_ready_for_counterpart_qa_review`

## Scope

This is an investigation/report-only EC-8 containment artifact. No `service.py` code, routing, answer text, final-answer authority, strict enforcement, live trace, deployment, staging, commit, or push action is included.

## Branch / Head

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Git state: detached post-merge main verification checkout (`HEAD (no branch)`)
- HEAD: `bd99c70` (`bd99c70dac7bf5a83e987cfacd4ddfff8a5c8efd`)
- Service file: `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

## Audit Method

- Parsed `service.py` with Python AST to enumerate top-level functions and constants.
- Scanned `ai_assistant_ui` Python files for direct `ai_assistant_ui.qwen_chat.service` imports and text references to public service symbols.
- Inspected `api.py` whitelist entry points to identify Frappe/API paths reaching service runtime.
- Classified symbols as active runtime entry, public API dependency, governance/test export, smoke/probe compatibility export, internal helper, or unknown owner.
- No symbol movement or facade extraction was performed.

## Summary

| Metric | Count |
| --- | ---: |
| `service.py` line count | 7809 |
| Public top-level functions | 215 |
| Private top-level helpers/wrappers | 220 |
| Public top-level constants | 2 |
| `run_*` smoke/probe/release-gate exports | 213 |
| Direct service import statements found | 1 |
| Future facade candidates | 214 |
| Unknown-owner symbols | 0 |

## Classification Counts

| Classification | Count |
| --- | ---: |
| active runtime entry | 1 |
| governance/test export | 55 |
| internal helper | 1 |
| public API dependency | 1 |
| smoke/probe compatibility export | 159 |

## Direct Public Callers / Imports

| Caller file | Line | Import/call surface | Classification |
| --- | ---: | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/api.py` | 5 | imports `QWEN_SESSION_DOCTYPE`, `handle_qwen_user_message` | public API/runtime dependency |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/phase8_hardening_support.py` | 147+ | injected `handle_qwen_user_message` callback references (17 text refs) | smoke/probe compatibility support, not a direct service import |

Directly imported service symbols are limited to `QWEN_SESSION_DOCTYPE` and `handle_qwen_user_message` in `api.py`. The `phase8_hardening_support.py` references are callback/injection support and should still be treated as compatibility-sensitive before extraction.

## Frappe / API Entry Points

| API function | Lines | Reaches service runtime | Service dependency |
| --- | ---: | --- | --- |
| `get_qwen_sessions` | 15-23 | no | `QWEN_SESSION_DOCTYPE` or session CRUD only |
| `create_qwen_session` | 27-31 | no | `QWEN_SESSION_DOCTYPE` or session CRUD only |
| `rename_qwen_session` | 35-39 | no | `QWEN_SESSION_DOCTYPE` or session CRUD only |
| `delete_qwen_session` | 43-46 | no | `QWEN_SESSION_DOCTYPE` or session CRUD only |
| `get_qwen_messages` | 50-60 | no | `QWEN_SESSION_DOCTYPE` or session CRUD only |
| `qwen_chat_send` | 64-79 | yes | `handle_qwen_user_message` |

`qwen_chat_send` is the only whitelisted API entry point found to reach the active runtime service entry. The other API functions depend on the session doctype constant and must remain stable for API compatibility, but they do not execute `service.py` runtime handling.

## Stable Surface

| Symbol | Lines | Reason stable | Future extraction posture |
| --- | ---: | --- | --- |
| `handle_qwen_user_message` | 3776-5841 | Active runtime entry reached by `api.py::qwen_chat_send`; central service runtime path. | Must remain callable from existing API. Facade extraction requires compatibility wrapper and caller proof. |
| `QWEN_SESSION_DOCTYPE` | 647 | Imported by `api.py` session CRUD and send paths. | Keep stable or re-export from future facade. |
| `run_*` smoke/probe/release-gate exports | 5844-7809 region | Governance, release-gate, and smoke/probe compatibility surface. | Candidate for future smoke/governance facade, but not safe to move without external caller scan and re-export plan. |
| `summarize_compiled_first_turn_audits` | 5852-5861 | Public governance/test export adjacent to run wrappers. | Candidate for governance facade with compatibility wrapper. |

## Future Facade Extraction Candidates

- `214` public functions are candidates for future facade extraction, mostly smoke/probe/release-gate and governance exports after line 5844.
- Candidate extraction direction: move smoke/probe/release-gate exports behind a compatibility facade while keeping `service.py` re-exports until caller evidence is complete.
- `handle_qwen_user_message` is not an extraction candidate in EC-8-B; it is the active service runtime entry and needs deeper containment planning first.
- `VISIBLE_ROLES` is currently internal helper surface with no direct external importer found; it can be reviewed later if containment work touches role/session visibility helpers.

## Symbols Requiring Further Caller Evidence Before Touching

- All `run_*` exports require evidence from scripts, governance reports, tests, and any external operator docs before movement.
- `phase8_hardening_support.py` injected `handle_qwen_user_message` usage should be preserved through any future facade/compatibility strategy.
- The AST caller scan was limited by existing non-printable/BOM parse errors in `manual_uat_evidence.py`, `test_manual_uat_evidence_contracts.py`, and `test_regression_scenario_packs.py`; this is a known syntax-scan limitation and not fixed in EC-8-B.
- Service private authority helpers around policy/control emission should not be moved until final-answer authority trace ownership is revalidated.

## Parse-Limited Files

| File | Reason | EC-8-B treatment |
| --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_evidence.py` | invalid non-printable character U+FEFF (<unknown>, line 1) | Caller scan limitation only; no fix in this slice. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_evidence_contracts.py` | invalid non-printable character U+FEFF (<unknown>, line 1) | Caller scan limitation only; no fix in this slice. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_regression_scenario_packs.py` | invalid non-printable character U+FEFF (<unknown>, line 1) | Caller scan limitation only; no fix in this slice. |

## Constants Inventory

| Constant | Line | Classification | Must remain stable | Direct importers |
| --- | ---: | --- | --- | --- |
| `QWEN_SESSION_DOCTYPE` | 647 | public API dependency | yes | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/api.py` |
| `VISIBLE_ROLES` | 648 | internal helper | no current external importer found | none found |

## Complete Public Function Inventory

| Function | Lines | Classification | Must remain stable | Facade candidate | Direct importers |
| --- | ---: | --- | --- | --- | --- |
| `handle_qwen_user_message` | 3776-5841 | active runtime entry | yes | no | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/api.py` |
| `run_phase4_compiled_rollout_smoke` | 5844-5845 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4_compiled_rollout_governance_selftests` | 5848-5849 | governance/test export | yes | yes | none found |
| `summarize_compiled_first_turn_audits` | 5852-5861 | governance/test export | yes | yes | none found |
| `run_phase4_compiled_rollout_monitoring_smoke` | 5864-5865 | smoke/probe compatibility export | yes | yes | none found |
| `run_first_turn_regression_suite` | 5868-5869 | governance/test export | yes | yes | none found |
| `run_same_session_fresh_query_regression_smoke` | 5872-5873 | governance/test export | yes | yes | none found |
| `run_phase4b_followup_fidelity_smoke` | 5876-5884 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_transaction_listing_smoke` | 5887-5894 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_delivery_note_listing_smoke` | 5897-5904 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_delivery_note_listing_limit_probe` | 5907-5914 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_delivery_note_detail_smoke` | 5917-5925 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_2_sales_order_detail_smoke` | 5928-5936 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_2_sales_order_status_followup_smoke` | 5939-5945 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_3_purchase_order_listing_smoke` | 5948-5955 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_3_purchase_order_status_scope_reset_smoke` | 5958-5966 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_3_purchase_order_detail_smoke` | 5969-5977 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_3_purchase_order_status_followup_smoke` | 5980-5986 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_4_customer_credit_exposure_smoke` | 5989-5997 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_4_customer_credit_overdue_smoke` | 6000-6008 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_4_customer_credit_overdue_probe` | 6011-6019 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_4_customer_credit_balance_smoke` | 6022-6030 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_4_customer_credit_detail_followup_smoke` | 6033-6039 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase3_3b_customer_detail_clarification_followup_smoke` | 6042-6050 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase3_3c_customer_master_lookup_smoke` | 6053-6054 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase_d2a_transaction_listing_today_requery_smoke` | 6057-6058 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase_d2c_transaction_listing_base_scope_reset_smoke` | 6061-6062 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase_e2_1b_purchase_invoice_listing_smoke` | 6177-6180 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase_e2_4_purchase_receipt_listing_smoke` | 6183-6186 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase_e3_2_payment_entry_listing_smoke` | 6189-6192 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase_e1_4_item_master_activation_smoke` | 6195-6198 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase_e1_5_item_deictic_continuity_smoke` | 6201-6204 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase_e1_6_item_inventory_followup_debug_smoke` | 6207-6210 | governance/test export | yes | yes | none found |
| `run_h3_targeted_restore_prefers_item_collection_over_newer_detail_smoke` | 6213-6216 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_targeted_restore_prefers_item_collection_over_newer_detail_smoke` | 6219-6222 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_4_customer_credit_policy_followup_smoke` | 6225-6231 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_4_customer_credit_policy_followup_probe` | 6234-6240 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_4_customer_credit_balance_probe` | 6243-6251 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_4_customer_credit_scope_reset_smoke` | 6254-6262 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_4_customer_credit_scope_reset_probe` | 6265-6275 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase2_4_governed_kpi_frontdoor_smoke` | 6278-6284 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase2_4_governed_kpi_frontdoor_probe` | 6287-6288 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase2_5_governed_kpi_period_execution_smoke` | 6291-6297 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase2_5_governed_kpi_period_execution_probe` | 6300-6301 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase2_5_governed_kpi_customer_execution_smoke` | 6304-6310 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase2_5_governed_kpi_customer_execution_probe` | 6313-6314 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase3_2_customer_commercial_composite_smoke` | 6317-6323 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase3_2_customer_commercial_composite_probe` | 6326-6327 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase3_2_projection_followup_debug` | 6330-6331 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase3_2_subject_switch_regression_debug` | 6334-6335 | governance/test export | yes | yes | none found |
| `run_phase3_3_ranking_projection_continuation_regression_debug` | 6338-6339 | governance/test export | yes | yes | none found |
| `run_phase3_3_product_quantity_projection_regression_debug` | 6342-6343 | governance/test export | yes | yes | none found |
| `run_phase1_1_delivery_note_date_scope_probe` | 6346-6353 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_delivery_note_date_scope_smoke` | 6356-6363 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_delivery_note_status_probe` | 6366-6373 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_delivery_note_status_smoke` | 6376-6383 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_delivery_note_session_reset_smoke` | 6386-6393 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_delivery_note_invoice_switch_debug` | 6396-6397 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_invoice_detail_delivery_trend_debug` | 6400-6401 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_invoice_detail_delivery_trend_smoke` | 6404-6405 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_delivery_note_trend_probe` | 6408-6416 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_delivery_note_trend_smoke` | 6419-6428 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_delivery_note_last_year_trend_smoke` | 6431-6444 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_family_evaluation_suite` | 6486-6497 | governance/test export | yes | yes | none found |
| `run_phase4b_family_evaluation_smoke` | 6500-6504 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_full_family_evaluation_suite` | 6507-6512 | governance/test export | yes | yes | none found |
| `run_phase4b_full_family_evaluation_smoke` | 6515-6518 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_family_latency_budget_report` | 6521-6526 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_family_latency_budget_smoke` | 6529-6532 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_family_tool_surface_smoke` | 6535-6543 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_family_tool_surface_probe` | 6546-6549 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_clarification_translation_probe` | 6552-6555 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_response_policy_probe` | 6558-6562 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_clarification_policy_smoke` | 6565-6570 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_natural_narrative_smoke` | 6573-6583 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_structured_presentation_smoke` | 6586-6592 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_context_isolation_smoke` | 6595-6601 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_entity_drilldown_smoke` | 6604-6610 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_invoice_delivery_proof_smoke` | 6613-6621 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase1_1_fresh_chat_invoice_delivery_proof_smoke` | 6624-6630 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_followup_report_ambiguity_smoke` | 6633-6639 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase4b_entity_drilldown_probe` | 6642-6652 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase55_clarification_attempt_smoke` | 6673-6681 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase55_clarification_meta_question_smoke` | 6684-6692 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase55_pending_override_smoke` | 6695-6703 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase55_frontdoor_boundary_smoke` | 6706-6714 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase55_ap_ar_default_policy_smoke` | 6717-6725 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase55_hardening_suite` | 6728-6736 | governance/test export | yes | yes | none found |
| `run_phase55_observability_smoke` | 6739-6746 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase6_reasoning_live_rollout_smoke` | 6749-6750 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase6_reasoning_without_grounding_smoke` | 6753-6762 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase6_reasoning_frontdoor_boundary_smoke` | 6765-6773 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase6_nonadvisory_recommendation_boundary_smoke` | 6776-6785 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase6_artifact_refinement_precedence_smoke` | 6788-6796 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase6_continuation_fulfillment_smoke` | 6799-6805 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase6_grounded_source_reset_smoke` | 6808-6816 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase6_observability_smoke` | 6819-6826 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase6_hardening_suite` | 6829-6841 | governance/test export | yes | yes | none found |
| `run_phase7_hardening_suite` | 6844-6848 | governance/test export | yes | yes | none found |
| `run_phase6_reasoning_live_debug` | 6851-6852 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase7c_live_boundary_orchestration_smoke` | 6855-6863 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase7d_boundary_response_live_smoke` | 6866-6876 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase7_observability_smoke` | 6879-6889 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase8b_recovery_authority_smoke` | 6892-6899 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase8_recovery_guidance_observability_smoke` | 6902-6914 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase8_evidence_boundary_observability_smoke` | 6917-6924 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase8_enrichment_boundary_observability_smoke` | 6927-6934 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase8c_repair_handling_smoke` | 6937-6951 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase8c_repair_handling_debug` | 6954-6955 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase8d_fresh_query_override_smoke` | 6958-6972 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase8_recovery_execution_smoke` | 6975-6984 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase8_recovery_execution_debug` | 6987-6988 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_duplicate_recovery_acceptance_smoke` | 7018-7021 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_stale_recovery_invalidated_by_fresh_override_smoke` | 7024-7027 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_post_stop_clarification_repeat_smoke` | 7030-7033 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_clarification_preempts_recovery_smoke` | 7036-7039 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_clarification_resolution_does_not_resurrect_stale_recovery_smoke` | 7042-7045 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_fresh_query_replaces_grounded_context_smoke` | 7048-7051 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_pending_override_replaces_with_new_grounded_context_smoke` | 7054-7057 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_master_data_pending_override_switches_focus_smoke` | 7060-7063 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_option_list_then_override_switches_focus_smoke` | 7066-7069 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_branch_restore_reopens_pending_clarification_smoke` | 7072-7075 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_question_restore_reopens_pending_clarification_smoke` | 7078-7081 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_branch_restore_prefers_newer_focus_smoke` | 7084-7087 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_branch_restore_prefers_newer_focus_smoke` | 7091-7094 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke` | 7097-7100 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke` | 7104-7107 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_question_restore_prefers_newer_focus_smoke` | 7111-7114 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_targeted_restore_prefers_named_branch_smoke` | 7117-7120 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_targeted_restore_prefers_collection_branch_over_newer_detail_smoke` | 7123-7126 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_targeted_restore_prefers_customer_collection_over_newer_detail_smoke` | 7129-7132 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke` | 7135-7138 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke` | 7141-7144 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke` | 7147-7150 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke` | 7153-7156 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke` | 7159-7162 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke` | 7165-7168 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_pending_discard_redirects_to_fresh_supplier_focus_smoke` | 7171-7174 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_soft_chained_pending_redirect_to_fresh_supplier_focus_smoke` | 7177-7180 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_pending_discard_redirects_to_balance_sheet_smoke` | 7184-7187 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_ambiguous_item_list_to_stock_followup_smoke` | 7190-7193 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_option_list_that_you_found_to_stock_followup_smoke` | 7196-7199 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_exact_item_focus_stock_followup_smoke` | 7202-7205 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_seeded_transaction_document_followup_smoke` | 7209-7212 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_financial_statement_switch_followup_smoke` | 7215-7218 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_master_data_single_row_detail_followup_smoke` | 7221-7224 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_active_sequence_override_clears_prior_sequence_smoke` | 7227-7230 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_targeted_restore_recovers_historical_branch_over_active_sequence_smoke` | 7233-7236 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_targeted_restore_recovers_historical_branch_over_active_sequence_smoke` | 7239-7242 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_pronoun_discard_targeted_restore_over_active_sequence_smoke` | 7245-7248 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_targeted_restore_replays_resumable_prior_recovery_smoke` | 7251-7254 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_smoke` | 7258-7261 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke` | 7265-7268 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke` | 7272-7275 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_targeted_restore_smoke` | 7279-7383 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_question_restore_resumes_active_sequence_smoke` | 7387-7390 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_question_restore_resumes_active_sequence_smoke` | 7394-7397 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_pronoun_discard_question_restore_resumes_active_sequence_smoke` | 7400-7403 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_discard_prefixed_question_restore_smoke` | 7407-7482 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_latest_fresh_grounded_query_wins_smoke` | 7486-7489 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_repeated_identical_fresh_query_replaces_grounding_smoke` | 7492-7495 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_repeated_identical_composite_grounded_query_replaces_grounding_smoke` | 7498-7501 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_latest_seeded_recovery_wins_smoke` | 7504-7507 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_newer_recovery_survives_older_consumed_recovery_smoke` | 7510-7513 | smoke/probe compatibility export | yes | yes | none found |
| `run_h3_duplicate_acceptance_after_newer_recovery_execution_smoke` | 7516-7519 | smoke/probe compatibility export | yes | yes | none found |
| `run_phase8_hardening_suite` | 7522-7528 | governance/test export | yes | yes | none found |
| `run_h4_inferred_operational_evidence_stays_bounded_smoke` | 7531-7534 | smoke/probe compatibility export | yes | yes | none found |
| `run_h4_mixed_metric_request_stays_bounded_smoke` | 7537-7540 | smoke/probe compatibility export | yes | yes | none found |
| `run_h4_long_multisentence_followup_stays_bounded_smoke` | 7543-7546 | smoke/probe compatibility export | yes | yes | none found |
| `run_h4_creative_followup_after_reasoning_is_refused_smoke` | 7549-7552 | smoke/probe compatibility export | yes | yes | none found |
| `run_h4_recommendation_guarantee_stays_bounded_smoke` | 7555-7558 | smoke/probe compatibility export | yes | yes | none found |
| `run_h4_adversarial_suite` | 7561-7564 | governance/test export | yes | yes | none found |
| `run_h5_release_gate_rollout_probe` | 7567-7570 | governance/test export | yes | yes | none found |
| `run_h5_release_gate_sanity_pack` | 7573-7576 | governance/test export | yes | yes | none found |
| `run_h5_release_gate_suite` | 7579-7582 | governance/test export | yes | yes | none found |
| `run_post_contract_regression_suite` | 7585-7588 | governance/test export | yes | yes | none found |
| `run_nbu_s7_same_session_fresh_query_matrix_smoke` | 7591-7592 | smoke/probe compatibility export | yes | yes | none found |
| `run_nbu_s7_visible_context_latest_artifact_smoke` | 7595-7596 | smoke/probe compatibility export | yes | yes | none found |
| `run_nbu_s7_safe_boundary_language_smoke` | 7599-7600 | smoke/probe compatibility export | yes | yes | none found |
| `run_bounded_release_gate` | 7650-7660 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_phase1_core` | 7663-7664 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_phase1_document_detail` | 7667-7668 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_phase1_order_followup` | 7671-7672 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_phase1_customer_credit` | 7675-7676 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_release_sanity` | 7679-7680 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_nbu_s7_regression_matrix` | 7683-7684 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_nbu_s7_context_matrix` | 7687-7688 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_nbu_s7_projection_matrix` | 7691-7692 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_nbu_s7_boundary_recovery_matrix` | 7695-7696 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_nbu_s7_safe_boundary_language` | 7699-7700 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_suites` | 7703-7704 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase55` | 7707-7708 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6` | 7711-7712 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6_aggregate` | 7715-7716 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6_recommendation_policy` | 7719-7720 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6_reasoning_live_rollout` | 7723-7724 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6_reasoning_without_grounding` | 7727-7728 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6_reasoning_frontdoor_boundary` | 7731-7732 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6_nonadvisory_recommendation_boundary` | 7735-7736 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6_artifact_refinement_precedence` | 7739-7740 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6_continuation_fulfillment` | 7743-7744 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6_grounded_source_reset` | 7747-7748 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6_continuation_guardrail` | 7751-7752 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase6_observability` | 7755-7756 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase7` | 7759-7760 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase7_aggregate` | 7763-7764 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase7_live_boundary_orchestration` | 7767-7768 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase7_boundary_response_live` | 7771-7772 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase8` | 7775-7776 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase8_aggregate` | 7779-7780 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase8_recovery_authority` | 7783-7784 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase8_repair_handling` | 7787-7788 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase8_fresh_query_override` | 7791-7792 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_post_contract_phase8_recovery_execution` | 7795-7796 | governance/test export | yes | yes | none found |
| `run_bounded_release_gate_inventory` | 7799-7809 | governance/test export | yes | yes | none found |

## Verification Summary

| Check | Result |
| --- | --- |
| Guardrail | PASS (`python3 scripts/check_qwen_enterprise_guardrails.py`) |
| Fake-Frappe service import | PASS |
| `service.py` compile | PASS |
| Direct assistant inventory | PASS: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths_length=27` |
| Formal raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Scoped AI diff check | PASS (`git diff --check -- impl_factory/05_custom_logic/custom_app/ai_assistant_ui`) |
| Excluded status scan | PASS: no ERP UI, seed/data, temp/probe/cache, PrimeAxis, generated scratch, raw/redacted trace, site config, secret, or archive-content entries |
| Staged files | PASS: `0` |

No runtime/source behavior changes were made for EC-8-B. The only new file from this slice is this governance report.

## EC-8-B Decision

`ec_8_b_public_service_surface_caller_audit_ready_for_counterpart_qa_review`

## Recommended Next Step

After Counterpart/QA acceptance, proceed to an EC-8-C compatibility facade/extraction feasibility plan only. Do not extract helpers or refactor `service.py` until the facade plan identifies the exact stable exports, re-export strategy, and caller proof required for compatibility.
