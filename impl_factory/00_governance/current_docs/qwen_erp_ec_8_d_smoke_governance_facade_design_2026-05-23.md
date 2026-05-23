# EC-8-D Smoke/Governance Facade Design

Decision target: `ec_8_d_smoke_governance_facade_design_ready_for_counterpart_qa_review`

## Scope

This is a report/test-only design slice. It does not implement a facade, edit `service.py`, move imports, extract helpers, change routing, change answer text, touch final-answer authority, enable strict enforcement, deploy, stage, commit, or push.

## Branch / Head

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Git state: detached post-merge main verification checkout (`HEAD (no branch)`)
- HEAD: `bd99c70` (`bd99c70dac7bf5a83e987cfacd4ddfff8a5c8efd`)

## Proposed Future Facade

| Design item | Proposal |
| --- | --- |
| Future module path | `ai_assistant_ui/qwen_chat/service_smoke_governance_facade.py` |
| Purpose | Own smoke/probe/release-gate/governance wrapper exports currently concentrated in `service.py` after line 5844. |
| First implementation shape | New module defines/moves a tiny approved subset first; `service.py` keeps same public names as wrappers/re-exports. |
| Compatibility posture | Existing external imports from `ai_assistant_ui.qwen_chat.service` remain valid. New module is additive until all callers migrate. |
| Runtime posture | No active runtime branch movement. `handle_qwen_user_message` stays in `service.py`. |
| Authority/metadata posture | Final-answer authority and runtime metadata behavior remain untouched. |

## Candidate Ownership Boundary

| Candidate group | Count | Future facade ownership | Must remain re-exported from `service.py` | Notes |
| --- | ---: | --- | --- | --- |
| `run_*` smoke/probe/release-gate exports | 213 | yes, phased only | yes, all names | Candidate group starts at `run_phase4_compiled_rollout_smoke` and ends at `run_bounded_release_gate_inventory`. |
| Governance/test exports | 55 | yes, phased only | yes, all names | Includes bounded release gates and self-test wrappers; overlaps mostly with `run_*`. |
| Smoke/probe compatibility exports | 159 | yes, phased only | yes, all names | Smoke/probe wrappers may invoke active runtime but should remain compatibility exports, not active API entry points. |
| `summarize_compiled_first_turn_audits` | 1 | yes, low-risk after tests | yes | Non-`run_*` governance helper at lines `5852-5861`. |
| `handle_qwen_user_message` | 1 | no | stays native in `service.py` | Active runtime entry reached by `api.py::qwen_chat_send`; not part of facade extraction. |
| `QWEN_SESSION_DOCTYPE` | 1 | no | stays stable in `service.py` | API/session constant imported by `api.py`. |
| Session/message-history private wrappers | private helper cluster | no for this facade | not public | Active runtime ordering/save/payload helpers; defer to separate containment analysis. |

## Exact Compatibility Pattern

Future implementation, if later approved, should use a two-layer compatibility pattern:

1. Add `service_smoke_governance_facade.py` with selected wrapper implementation or delegation for an approved tiny subset.
2. Keep the original public names in `service.py`; each moved symbol remains importable from `ai_assistant_ui.qwen_chat.service`.
3. `service.py` wrappers may delegate to the facade, but must preserve function name, signature shape, return payload shape, exception behavior, and any injected callback semantics.
4. No `api.py` import path changes; `api.py` continues importing `QWEN_SESSION_DOCTYPE` and `handle_qwen_user_message` from `service.py`.
5. `phase8_hardening_support.py` callback/injection behavior must remain valid; facade work must not require it to import a new path.
6. The first implementation should be tiny and reversible, not a 214-export move.

## Caller Scan Required Before Implementation

- AST scan all Python files for `from ai_assistant_ui.qwen_chat.service import ...`, `import ai_assistant_ui.qwen_chat.service`, and dynamic service attribute access.
- Text scan scripts, governance docs, shell snippets, and release instructions for every proposed moved symbol.
- Special-case callback scan for `phase8_hardening_support.py` and any helper accepting `handle_qwen_user_message` as a parameter.
- Confirm no external scripts invoke moved names via `bench execute ai_assistant_ui.qwen_chat.service.<symbol>` without service re-export coverage.
- Confirm parse-limited files from EC-8-B are either fixed in a separate syntax cleanup gate or scanned textually before extraction.

## Test List Required Before Any Implementation

| Test category | Required proof |
| --- | --- |
| Public export inventory | All pre-existing public `service.py` names still exist after facade work. |
| Re-export compatibility | Importing moved names from `ai_assistant_ui.qwen_chat.service` still works. |
| Facade direct import | Importing moved names from `service_smoke_governance_facade.py` works if the new module is public. |
| Return-shape compatibility | Selected moved wrappers return exactly the same payload shape as before. |
| Phase8 callback compatibility | Existing callback/injection flows continue to accept and invoke `handle_qwen_user_message`. |
| Guardrail and authority | Guardrail PASS, direct assistant inventory `0 / 1 / 27`, raw append scan limited to authorized sinks. |
| Metadata/probe safety | Existing EC-7 metadata/probe/soft-gate focused tests remain green if touched. |
| Syntax/import safety | Fake-Frappe service import PASS, facade import PASS, Python compile PASS. |

## Future Staging Plan

| Future file/hunk | Staging approach | Rationale |
| --- | --- | --- |
| New `service_smoke_governance_facade.py` | full-file | New additive module can be whole-file staged once approved. |
| `service.py` wrapper/re-export edits | hunk-aware only | `service.py` contains active runtime; never whole-file stage. |
| Focused facade tests | full-file if new, hunk-aware if existing | Tests should be limited to compatibility and no behavior movement. |
| Governance report/proof | full-file | Audit trail for approved extraction slice. |
| Any runtime helper/module | not allowed in smoke/governance facade slice | Runtime extraction is outside this facade design. |

## Rollback Plan

- Keep first implementation additive and tiny so rollback can remove the new facade module and restore the touched `service.py` wrapper hunks.
- Because `service.py` keeps public names, failed caller migration should not break existing imports if re-export wrappers are preserved.
- If any compatibility test fails, stop before commit and revert only the approved facade hunks/new file; do not touch active runtime logic.
- If a post-merge issue appears, rollback commit should remove facade delegation while leaving `handle_qwen_user_message`, `QWEN_SESSION_DOCTYPE`, and authority helpers unchanged.

## Candidate Export Inventory

The candidate set for future facade ownership is the 214 public compatibility exports: 213 `run_*` exports plus `summarize_compiled_first_turn_audits`. All must remain re-exported from `service.py` during any transition.

| Symbol | Lines | Current classification | Future facade candidate |
| --- | ---: | --- | --- |
| `run_phase4_compiled_rollout_smoke` | 5844-5845 | smoke/probe compatibility export | yes, phased only |
| `run_phase4_compiled_rollout_governance_selftests` | 5848-5849 | governance/test export | yes, phased only |
| `run_phase4_compiled_rollout_monitoring_smoke` | 5864-5865 | smoke/probe compatibility export | yes, phased only |
| `run_first_turn_regression_suite` | 5868-5869 | governance/test export | yes, phased only |
| `run_same_session_fresh_query_regression_smoke` | 5872-5873 | governance/test export | yes, phased only |
| `run_phase4b_followup_fidelity_smoke` | 5876-5884 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_transaction_listing_smoke` | 5887-5894 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_delivery_note_listing_smoke` | 5897-5904 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_delivery_note_listing_limit_probe` | 5907-5914 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_delivery_note_detail_smoke` | 5917-5925 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_2_sales_order_detail_smoke` | 5928-5936 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_2_sales_order_status_followup_smoke` | 5939-5945 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_3_purchase_order_listing_smoke` | 5948-5955 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_3_purchase_order_status_scope_reset_smoke` | 5958-5966 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_3_purchase_order_detail_smoke` | 5969-5977 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_3_purchase_order_status_followup_smoke` | 5980-5986 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_4_customer_credit_exposure_smoke` | 5989-5997 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_4_customer_credit_overdue_smoke` | 6000-6008 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_4_customer_credit_overdue_probe` | 6011-6019 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_4_customer_credit_balance_smoke` | 6022-6030 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_4_customer_credit_detail_followup_smoke` | 6033-6039 | smoke/probe compatibility export | yes, phased only |
| `run_phase3_3b_customer_detail_clarification_followup_smoke` | 6042-6050 | smoke/probe compatibility export | yes, phased only |
| `run_phase3_3c_customer_master_lookup_smoke` | 6053-6054 | smoke/probe compatibility export | yes, phased only |
| `run_phase_d2a_transaction_listing_today_requery_smoke` | 6057-6058 | smoke/probe compatibility export | yes, phased only |
| `run_phase_d2c_transaction_listing_base_scope_reset_smoke` | 6061-6062 | smoke/probe compatibility export | yes, phased only |
| `run_phase_e2_1b_purchase_invoice_listing_smoke` | 6177-6180 | smoke/probe compatibility export | yes, phased only |
| `run_phase_e2_4_purchase_receipt_listing_smoke` | 6183-6186 | smoke/probe compatibility export | yes, phased only |
| `run_phase_e3_2_payment_entry_listing_smoke` | 6189-6192 | smoke/probe compatibility export | yes, phased only |
| `run_phase_e1_4_item_master_activation_smoke` | 6195-6198 | smoke/probe compatibility export | yes, phased only |
| `run_phase_e1_5_item_deictic_continuity_smoke` | 6201-6204 | smoke/probe compatibility export | yes, phased only |
| `run_phase_e1_6_item_inventory_followup_debug_smoke` | 6207-6210 | governance/test export | yes, phased only |
| `run_h3_targeted_restore_prefers_item_collection_over_newer_detail_smoke` | 6213-6216 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_targeted_restore_prefers_item_collection_over_newer_detail_smoke` | 6219-6222 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_4_customer_credit_policy_followup_smoke` | 6225-6231 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_4_customer_credit_policy_followup_probe` | 6234-6240 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_4_customer_credit_balance_probe` | 6243-6251 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_4_customer_credit_scope_reset_smoke` | 6254-6262 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_4_customer_credit_scope_reset_probe` | 6265-6275 | smoke/probe compatibility export | yes, phased only |
| `run_phase2_4_governed_kpi_frontdoor_smoke` | 6278-6284 | smoke/probe compatibility export | yes, phased only |
| `run_phase2_4_governed_kpi_frontdoor_probe` | 6287-6288 | smoke/probe compatibility export | yes, phased only |
| `run_phase2_5_governed_kpi_period_execution_smoke` | 6291-6297 | smoke/probe compatibility export | yes, phased only |
| `run_phase2_5_governed_kpi_period_execution_probe` | 6300-6301 | smoke/probe compatibility export | yes, phased only |
| `run_phase2_5_governed_kpi_customer_execution_smoke` | 6304-6310 | smoke/probe compatibility export | yes, phased only |
| `run_phase2_5_governed_kpi_customer_execution_probe` | 6313-6314 | smoke/probe compatibility export | yes, phased only |
| `run_phase3_2_customer_commercial_composite_smoke` | 6317-6323 | smoke/probe compatibility export | yes, phased only |
| `run_phase3_2_customer_commercial_composite_probe` | 6326-6327 | smoke/probe compatibility export | yes, phased only |
| `run_phase3_2_projection_followup_debug` | 6330-6331 | smoke/probe compatibility export | yes, phased only |
| `run_phase3_2_subject_switch_regression_debug` | 6334-6335 | governance/test export | yes, phased only |
| `run_phase3_3_ranking_projection_continuation_regression_debug` | 6338-6339 | governance/test export | yes, phased only |
| `run_phase3_3_product_quantity_projection_regression_debug` | 6342-6343 | governance/test export | yes, phased only |
| `run_phase1_1_delivery_note_date_scope_probe` | 6346-6353 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_delivery_note_date_scope_smoke` | 6356-6363 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_delivery_note_status_probe` | 6366-6373 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_delivery_note_status_smoke` | 6376-6383 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_delivery_note_session_reset_smoke` | 6386-6393 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_delivery_note_invoice_switch_debug` | 6396-6397 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_invoice_detail_delivery_trend_debug` | 6400-6401 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_invoice_detail_delivery_trend_smoke` | 6404-6405 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_delivery_note_trend_probe` | 6408-6416 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_delivery_note_trend_smoke` | 6419-6428 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_delivery_note_last_year_trend_smoke` | 6431-6444 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_family_evaluation_suite` | 6486-6497 | governance/test export | yes, phased only |
| `run_phase4b_family_evaluation_smoke` | 6500-6504 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_full_family_evaluation_suite` | 6507-6512 | governance/test export | yes, phased only |
| `run_phase4b_full_family_evaluation_smoke` | 6515-6518 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_family_latency_budget_report` | 6521-6526 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_family_latency_budget_smoke` | 6529-6532 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_family_tool_surface_smoke` | 6535-6543 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_family_tool_surface_probe` | 6546-6549 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_clarification_translation_probe` | 6552-6555 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_response_policy_probe` | 6558-6562 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_clarification_policy_smoke` | 6565-6570 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_natural_narrative_smoke` | 6573-6583 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_structured_presentation_smoke` | 6586-6592 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_context_isolation_smoke` | 6595-6601 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_entity_drilldown_smoke` | 6604-6610 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_invoice_delivery_proof_smoke` | 6613-6621 | smoke/probe compatibility export | yes, phased only |
| `run_phase1_1_fresh_chat_invoice_delivery_proof_smoke` | 6624-6630 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_followup_report_ambiguity_smoke` | 6633-6639 | smoke/probe compatibility export | yes, phased only |
| `run_phase4b_entity_drilldown_probe` | 6642-6652 | smoke/probe compatibility export | yes, phased only |
| `run_phase55_clarification_attempt_smoke` | 6673-6681 | smoke/probe compatibility export | yes, phased only |
| `run_phase55_clarification_meta_question_smoke` | 6684-6692 | smoke/probe compatibility export | yes, phased only |
| `run_phase55_pending_override_smoke` | 6695-6703 | smoke/probe compatibility export | yes, phased only |
| `run_phase55_frontdoor_boundary_smoke` | 6706-6714 | smoke/probe compatibility export | yes, phased only |
| `run_phase55_ap_ar_default_policy_smoke` | 6717-6725 | smoke/probe compatibility export | yes, phased only |
| `run_phase55_hardening_suite` | 6728-6736 | governance/test export | yes, phased only |
| `run_phase55_observability_smoke` | 6739-6746 | smoke/probe compatibility export | yes, phased only |
| `run_phase6_reasoning_live_rollout_smoke` | 6749-6750 | smoke/probe compatibility export | yes, phased only |
| `run_phase6_reasoning_without_grounding_smoke` | 6753-6762 | smoke/probe compatibility export | yes, phased only |
| `run_phase6_reasoning_frontdoor_boundary_smoke` | 6765-6773 | smoke/probe compatibility export | yes, phased only |
| `run_phase6_nonadvisory_recommendation_boundary_smoke` | 6776-6785 | smoke/probe compatibility export | yes, phased only |
| `run_phase6_artifact_refinement_precedence_smoke` | 6788-6796 | smoke/probe compatibility export | yes, phased only |
| `run_phase6_continuation_fulfillment_smoke` | 6799-6805 | smoke/probe compatibility export | yes, phased only |
| `run_phase6_grounded_source_reset_smoke` | 6808-6816 | smoke/probe compatibility export | yes, phased only |
| `run_phase6_observability_smoke` | 6819-6826 | smoke/probe compatibility export | yes, phased only |
| `run_phase6_hardening_suite` | 6829-6841 | governance/test export | yes, phased only |
| `run_phase7_hardening_suite` | 6844-6848 | governance/test export | yes, phased only |
| `run_phase6_reasoning_live_debug` | 6851-6852 | smoke/probe compatibility export | yes, phased only |
| `run_phase7c_live_boundary_orchestration_smoke` | 6855-6863 | smoke/probe compatibility export | yes, phased only |
| `run_phase7d_boundary_response_live_smoke` | 6866-6876 | smoke/probe compatibility export | yes, phased only |
| `run_phase7_observability_smoke` | 6879-6889 | smoke/probe compatibility export | yes, phased only |
| `run_phase8b_recovery_authority_smoke` | 6892-6899 | smoke/probe compatibility export | yes, phased only |
| `run_phase8_recovery_guidance_observability_smoke` | 6902-6914 | smoke/probe compatibility export | yes, phased only |
| `run_phase8_evidence_boundary_observability_smoke` | 6917-6924 | smoke/probe compatibility export | yes, phased only |
| `run_phase8_enrichment_boundary_observability_smoke` | 6927-6934 | smoke/probe compatibility export | yes, phased only |
| `run_phase8c_repair_handling_smoke` | 6937-6951 | smoke/probe compatibility export | yes, phased only |
| `run_phase8c_repair_handling_debug` | 6954-6955 | smoke/probe compatibility export | yes, phased only |
| `run_phase8d_fresh_query_override_smoke` | 6958-6972 | smoke/probe compatibility export | yes, phased only |
| `run_phase8_recovery_execution_smoke` | 6975-6984 | smoke/probe compatibility export | yes, phased only |
| `run_phase8_recovery_execution_debug` | 6987-6988 | smoke/probe compatibility export | yes, phased only |
| `run_h3_duplicate_recovery_acceptance_smoke` | 7018-7021 | smoke/probe compatibility export | yes, phased only |
| `run_h3_stale_recovery_invalidated_by_fresh_override_smoke` | 7024-7027 | smoke/probe compatibility export | yes, phased only |
| `run_h3_post_stop_clarification_repeat_smoke` | 7030-7033 | smoke/probe compatibility export | yes, phased only |
| `run_h3_clarification_preempts_recovery_smoke` | 7036-7039 | smoke/probe compatibility export | yes, phased only |
| `run_h3_clarification_resolution_does_not_resurrect_stale_recovery_smoke` | 7042-7045 | smoke/probe compatibility export | yes, phased only |
| `run_h3_fresh_query_replaces_grounded_context_smoke` | 7048-7051 | smoke/probe compatibility export | yes, phased only |
| `run_h3_pending_override_replaces_with_new_grounded_context_smoke` | 7054-7057 | smoke/probe compatibility export | yes, phased only |
| `run_h3_master_data_pending_override_switches_focus_smoke` | 7060-7063 | smoke/probe compatibility export | yes, phased only |
| `run_h3_option_list_then_override_switches_focus_smoke` | 7066-7069 | smoke/probe compatibility export | yes, phased only |
| `run_h3_branch_restore_reopens_pending_clarification_smoke` | 7072-7075 | smoke/probe compatibility export | yes, phased only |
| `run_h3_question_restore_reopens_pending_clarification_smoke` | 7078-7081 | smoke/probe compatibility export | yes, phased only |
| `run_h3_branch_restore_prefers_newer_focus_smoke` | 7084-7087 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_branch_restore_prefers_newer_focus_smoke` | 7091-7094 | smoke/probe compatibility export | yes, phased only |
| `run_h3_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke` | 7097-7100 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_branch_restore_prefers_recent_focus_over_historical_prior_focus_smoke` | 7104-7107 | smoke/probe compatibility export | yes, phased only |
| `run_h3_question_restore_prefers_newer_focus_smoke` | 7111-7114 | smoke/probe compatibility export | yes, phased only |
| `run_h3_targeted_restore_prefers_named_branch_smoke` | 7117-7120 | smoke/probe compatibility export | yes, phased only |
| `run_h3_targeted_restore_prefers_collection_branch_over_newer_detail_smoke` | 7123-7126 | smoke/probe compatibility export | yes, phased only |
| `run_h3_targeted_restore_prefers_customer_collection_over_newer_detail_smoke` | 7129-7132 | smoke/probe compatibility export | yes, phased only |
| `run_h3_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke` | 7135-7138 | smoke/probe compatibility export | yes, phased only |
| `run_h3_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke` | 7141-7144 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_targeted_restore_prefers_sales_invoice_listing_over_newer_detail_smoke` | 7147-7150 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_targeted_restore_prefers_purchase_order_listing_over_newer_detail_smoke` | 7153-7156 | smoke/probe compatibility export | yes, phased only |
| `run_h3_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke` | 7159-7162 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_targeted_restore_recovers_sales_invoice_listing_over_newer_purchase_order_listing_smoke` | 7165-7168 | smoke/probe compatibility export | yes, phased only |
| `run_h3_pending_discard_redirects_to_fresh_supplier_focus_smoke` | 7171-7174 | smoke/probe compatibility export | yes, phased only |
| `run_h3_soft_chained_pending_redirect_to_fresh_supplier_focus_smoke` | 7177-7180 | smoke/probe compatibility export | yes, phased only |
| `run_h3_pending_discard_redirects_to_balance_sheet_smoke` | 7184-7187 | smoke/probe compatibility export | yes, phased only |
| `run_h3_ambiguous_item_list_to_stock_followup_smoke` | 7190-7193 | smoke/probe compatibility export | yes, phased only |
| `run_h3_option_list_that_you_found_to_stock_followup_smoke` | 7196-7199 | smoke/probe compatibility export | yes, phased only |
| `run_h3_exact_item_focus_stock_followup_smoke` | 7202-7205 | smoke/probe compatibility export | yes, phased only |
| `run_h3_seeded_transaction_document_followup_smoke` | 7209-7212 | smoke/probe compatibility export | yes, phased only |
| `run_h3_financial_statement_switch_followup_smoke` | 7215-7218 | smoke/probe compatibility export | yes, phased only |
| `run_h3_master_data_single_row_detail_followup_smoke` | 7221-7224 | smoke/probe compatibility export | yes, phased only |
| `run_h3_active_sequence_override_clears_prior_sequence_smoke` | 7227-7230 | smoke/probe compatibility export | yes, phased only |
| `run_h3_targeted_restore_recovers_historical_branch_over_active_sequence_smoke` | 7233-7236 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_targeted_restore_recovers_historical_branch_over_active_sequence_smoke` | 7239-7242 | smoke/probe compatibility export | yes, phased only |
| `run_h3_pronoun_discard_targeted_restore_over_active_sequence_smoke` | 7245-7248 | smoke/probe compatibility export | yes, phased only |
| `run_h3_targeted_restore_replays_resumable_prior_recovery_smoke` | 7251-7254 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_smoke` | 7258-7261 | smoke/probe compatibility export | yes, phased only |
| `run_h3_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke` | 7265-7268 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_targeted_restore_replays_resumable_prior_recovery_over_active_sequence_smoke` | 7272-7275 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_targeted_restore_smoke` | 7279-7383 | smoke/probe compatibility export | yes, phased only |
| `run_h3_question_restore_resumes_active_sequence_smoke` | 7387-7390 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_question_restore_resumes_active_sequence_smoke` | 7394-7397 | smoke/probe compatibility export | yes, phased only |
| `run_h3_pronoun_discard_question_restore_resumes_active_sequence_smoke` | 7400-7403 | smoke/probe compatibility export | yes, phased only |
| `run_h3_discard_prefixed_question_restore_smoke` | 7407-7482 | smoke/probe compatibility export | yes, phased only |
| `run_h3_latest_fresh_grounded_query_wins_smoke` | 7486-7489 | smoke/probe compatibility export | yes, phased only |
| `run_h3_repeated_identical_fresh_query_replaces_grounding_smoke` | 7492-7495 | smoke/probe compatibility export | yes, phased only |
| `run_h3_repeated_identical_composite_grounded_query_replaces_grounding_smoke` | 7498-7501 | smoke/probe compatibility export | yes, phased only |
| `run_h3_latest_seeded_recovery_wins_smoke` | 7504-7507 | smoke/probe compatibility export | yes, phased only |
| `run_h3_newer_recovery_survives_older_consumed_recovery_smoke` | 7510-7513 | smoke/probe compatibility export | yes, phased only |
| `run_h3_duplicate_acceptance_after_newer_recovery_execution_smoke` | 7516-7519 | smoke/probe compatibility export | yes, phased only |
| `run_phase8_hardening_suite` | 7522-7528 | governance/test export | yes, phased only |
| `run_h4_inferred_operational_evidence_stays_bounded_smoke` | 7531-7534 | smoke/probe compatibility export | yes, phased only |
| `run_h4_mixed_metric_request_stays_bounded_smoke` | 7537-7540 | smoke/probe compatibility export | yes, phased only |
| `run_h4_long_multisentence_followup_stays_bounded_smoke` | 7543-7546 | smoke/probe compatibility export | yes, phased only |
| `run_h4_creative_followup_after_reasoning_is_refused_smoke` | 7549-7552 | smoke/probe compatibility export | yes, phased only |
| `run_h4_recommendation_guarantee_stays_bounded_smoke` | 7555-7558 | smoke/probe compatibility export | yes, phased only |
| `run_h4_adversarial_suite` | 7561-7564 | governance/test export | yes, phased only |
| `run_h5_release_gate_rollout_probe` | 7567-7570 | governance/test export | yes, phased only |
| `run_h5_release_gate_sanity_pack` | 7573-7576 | governance/test export | yes, phased only |
| `run_h5_release_gate_suite` | 7579-7582 | governance/test export | yes, phased only |
| `run_post_contract_regression_suite` | 7585-7588 | governance/test export | yes, phased only |
| `run_nbu_s7_same_session_fresh_query_matrix_smoke` | 7591-7592 | smoke/probe compatibility export | yes, phased only |
| `run_nbu_s7_visible_context_latest_artifact_smoke` | 7595-7596 | smoke/probe compatibility export | yes, phased only |
| `run_nbu_s7_safe_boundary_language_smoke` | 7599-7600 | smoke/probe compatibility export | yes, phased only |
| `run_bounded_release_gate` | 7650-7660 | governance/test export | yes, phased only |
| `run_bounded_release_gate_phase1_core` | 7663-7664 | governance/test export | yes, phased only |
| `run_bounded_release_gate_phase1_document_detail` | 7667-7668 | governance/test export | yes, phased only |
| `run_bounded_release_gate_phase1_order_followup` | 7671-7672 | governance/test export | yes, phased only |
| `run_bounded_release_gate_phase1_customer_credit` | 7675-7676 | governance/test export | yes, phased only |
| `run_bounded_release_gate_release_sanity` | 7679-7680 | governance/test export | yes, phased only |
| `run_bounded_release_gate_nbu_s7_regression_matrix` | 7683-7684 | governance/test export | yes, phased only |
| `run_bounded_release_gate_nbu_s7_context_matrix` | 7687-7688 | governance/test export | yes, phased only |
| `run_bounded_release_gate_nbu_s7_projection_matrix` | 7691-7692 | governance/test export | yes, phased only |
| `run_bounded_release_gate_nbu_s7_boundary_recovery_matrix` | 7695-7696 | governance/test export | yes, phased only |
| `run_bounded_release_gate_nbu_s7_safe_boundary_language` | 7699-7700 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_suites` | 7703-7704 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase55` | 7707-7708 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6` | 7711-7712 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6_aggregate` | 7715-7716 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6_recommendation_policy` | 7719-7720 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6_reasoning_live_rollout` | 7723-7724 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6_reasoning_without_grounding` | 7727-7728 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6_reasoning_frontdoor_boundary` | 7731-7732 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6_nonadvisory_recommendation_boundary` | 7735-7736 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6_artifact_refinement_precedence` | 7739-7740 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6_continuation_fulfillment` | 7743-7744 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6_grounded_source_reset` | 7747-7748 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6_continuation_guardrail` | 7751-7752 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase6_observability` | 7755-7756 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase7` | 7759-7760 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase7_aggregate` | 7763-7764 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase7_live_boundary_orchestration` | 7767-7768 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase7_boundary_response_live` | 7771-7772 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase8` | 7775-7776 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase8_aggregate` | 7779-7780 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase8_recovery_authority` | 7783-7784 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase8_repair_handling` | 7787-7788 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase8_fresh_query_override` | 7791-7792 | governance/test export | yes, phased only |
| `run_bounded_release_gate_post_contract_phase8_recovery_execution` | 7795-7796 | governance/test export | yes, phased only |
| `run_bounded_release_gate_inventory` | 7799-7809 | governance/test export | yes, phased only |
| `summarize_compiled_first_turn_audits` | 5852-5861 | governance/test export | yes, phased only |

## Non-Goals

- No facade module is created in EC-8-D.
- No `service.py` code changes are made in EC-8-D.
- No public exports are moved in EC-8-D.
- No active runtime branch, final-answer authority, runtime metadata, routing, answer text, deployment, staging, commit, or push work is included.

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

No runtime/source behavior changes were made for EC-8-D. The only new file from this slice is this governance report.

## EC-8-D Decision

`ec_8_d_smoke_governance_facade_design_ready_for_counterpart_qa_review`

## What Is Next

If EC-8-D is accepted, the next slice should be EC-8-E staged implementation approval request or a tiny first-facade implementation plan. Do not implement extraction until owner/Counterpart/QA explicitly approve that step.
