# EC-5A Release Packaging / Worktree Control Baseline Investigation

## Executive Decision

Recommendation:

`enterprise_cleanup_ec_5a_ready_for_counterpart_review`

EC-5A is investigation only. It classifies the dirty worktree for release packaging review and does not perform cleanup, staging, deletion, moves, commits, `.gitignore` changes, or implementation work.

## Baseline

- Branch: `feature/ai-assistant`
- Head: `154be1e`
- Pre-EC-5A dirty count: `308`
- Expected dirty count after adding this EC-5A note: `309`
- Inventory checksum: `17094df3a5bcd4cfd05d4dd966012380437647c91fcb42ba84eb0feca2b76342`
- Generated at UTC: `2026-05-16T03:33:29+00:00`

## Classification Summary

| Category | Count | Packaging recommendation |
|---|---:|---|
| `ec4_source_changes` | 28 | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `ec4_tests` | 47 | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `ec4_generated_evidence` | 1 | `archive_or_selected_version_policy_required_before_packaging` |
| `s7_ec_governance_docs` | 79 | `version_or_archive_by_governance_policy_after_review` |
| `pre_existing_ai_changes` | 60 | `separate_ai_change_stream_owner_review_required` |
| `unrelated_erp_ui_changes` | 39 | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `seed_data_scripts` | 25 | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `temp_cache_probe_files` | 24 | `ignore_or_remove_candidate_after_owner_approval_only` |
| `unknown_review_required_files` | 5 | `owner_decision_required_before_packaging` |

- Classified dirty entries: `308`
- Unclassified dirty entries: `0`
- Unknown/review-required entries: `5`

## Packaging Groups

- Version candidates after review: `ec4_source_changes`, `ec4_tests`, selected `s7_ec_governance_docs`.
- Archive or selected-version policy required: `ec4_generated_evidence`, broader S7/EC generated evidence under `current_docs/generated/`.
- Exclude from EC bundle: `unrelated_erp_ui_changes`, `seed_data_scripts`, `temp_cache_probe_files`.
- Separate owner review required: `pre_existing_ai_changes`, `unknown_review_required_files`, unrelated ERP UI, seed/data scripts.
- Ignore/remove candidates only after approval: temp folders, probe files, screenshots, local Codex/Qwen scratch folders.

## Owner Decision List

- `pre_existing_ai_changes`: `60` entries require owner/reviewer policy before packaging action.
- `unrelated_erp_ui_changes`: `39` entries require owner/reviewer policy before packaging action.
- `seed_data_scripts`: `25` entries require owner/reviewer policy before packaging action.
- `temp_cache_probe_files`: `24` entries require owner/reviewer policy before packaging action.
- `unknown_review_required_files`: `5` entries require owner/reviewer policy before packaging action.
- `ec4_generated_evidence`: `1` entries require owner/reviewer policy before packaging action.

## Non-Goals

- `no implementation changes`
- `no cleanup`
- `no delete or move`
- `no staging or commit`
- `no .gitignore change`
- `no release packaging action`
- `no UX, Filter, MI, or family expansion`
- `no model-role strict enforcement`
- `no broad service.py refactor`

## Full Dirty Inventory By Category

### ec4_source_changes (28)

| Status | Path | Recommendation |
|---|---|---|
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/runtime_gate_lane.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/local_followup_support.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_activation.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recovery_guidance_support.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_trace_inspection.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support_emission_mapping.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/enterprise_cleanup_gate_report.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_emission_mapping.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_emission_closure_checkpoint.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_emission_dry_run.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_emission_leakage_audit.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_remaining_append_mapping.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_emission_mapping.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/legacy_runtime_emission_mapping.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/nbu_governed_requery_emission_mapping.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/reasoning_lane_emission_mapping.py` | `version_candidate_ec4_source_bundle_after_counterpart_review` |

### ec4_tests (47)

| Status | Path | Recommendation |
|---|---|---|
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_artifact_boundary_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_compiled_support_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_compiled_support_emission_mapping_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_control_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_followup_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_followup_emission_mapping_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_authority_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_closure_checkpoint_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_dry_run_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_leakage_audit_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_remaining_append_mapping_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_emission_mapping_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_emission_mapping_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_local_followup_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_archive_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_browser_batch_cli_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_browser_batch_runner_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_bundle_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_capture_template_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_evidence_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_export_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_import_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_operator_capture_template_promotion_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_operator_evidence_cli_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_operator_runbook_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_promotion_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_real_evidence_intake_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_renderer_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_sample_fixture_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_workflow_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_coverage_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_observability_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_strict_readiness_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_nbu_governed_requery_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_nbu_governed_requery_emission_mapping_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_policy_boundary_response_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_policy_boundary_uniformity_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_reasoning_lane_emission_mapping_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_reasoning_lane_model_role_observability_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_regression_scenario_packs.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_regression_suite_governance_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_runtime_gate_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_control_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_policy_boundary_authorized_emission_contracts.py` | `version_candidate_ec4_test_bundle_after_counterpart_review` |

### ec4_generated_evidence (1)

| Status | Path | Recommendation |
|---|---|---|
| `??` | `impl_factory/00_governance/current_docs/generated/` | `archive_or_selected_version_policy_required_before_packaging` |

### s7_ec_governance_docs (79)

| Status | Path | Recommendation |
|---|---|---|
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_ec_0_baseline_write_scope_manifest_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_ec_1_product_projection_browser_evidence_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_ec_2_counterpart_acceptance_clarification_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_ec_2_enterprise_cleanup_gate_report_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_ec_3_final_answer_hard_gate_dry_run_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_ec_4_authorized_emission_helper_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_ec_4_final_answer_emission_authority_closure_2026-05-16.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_enterprise_cleanup_counterpart_approval_sequence_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_0_baseline_freeze_and_acceptance_criteria_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_1_context_authority_projection_repair_implementation_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_2_semantic_ownership_ledger_implementation_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_2a_requested_limit_cardinality_preservation_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_3_final_answer_authority_contract_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_3a_final_authority_trace_inspection_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_3b_trace_status_boolean_hygiene_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_4_policy_boundary_uniformity_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_4a_boundary_trace_unification_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_4b_boundary_wording_standardization_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_5a_model_role_observability_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_5b_model_role_strict_readiness_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_5c_model_role_coverage_expansion_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6a_regression_suite_governance_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6b_regression_scenario_packs_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6c_manual_uat_evidence_contract_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6d_manual_uat_renderer_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6e_manual_browser_uat_execution_workflow_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6f_manual_uat_artifact_export_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6g_turn_level_trace_recency_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6h_manual_uat_evidence_archive_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6i_manual_uat_evidence_import_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6j_manual_uat_operator_capture_template_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6k_manual_uat_evidence_bundle_roundtrip_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6l_manual_uat_sample_fixture_dry_run_bundle_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6m_manual_uat_evidence_promotion_boundary_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6n_operator_evidence_mode_capture_template_upgrade_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6o_real_evidence_intake_promotion_ready_bundle_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6p_operator_evidence_import_cli_runner_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6q_operator_evidence_bundle_uat_execution_runbook_2026-05-13.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6r_real_browser_uat_evidence_trial_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6s_multi_scenario_real_browser_evidence_batch_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6t_a_browser_runner_contract_hardening_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6t_browser_batch_resilience_runner_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_6u_browser_runner_cli_real_browser_batch_adapter_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_counterpart_review_notes_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_enterprise_stabilization_architecture_plan_2026-05-12.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_x1_release_baseline_file_manifest_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_x2_uat_pipeline_ownership_map_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_x3_scenario_evidence_closure_table_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_x4_final_answer_authority_closure_proof_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_x5_model_role_regression_boundary_closure_report_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/00_governance/current_docs/qwen_erp_s7_x6_enterprise_stabilization_closure_note_2026-05-14.md` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_archive.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_browser_batch_cli.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_browser_batch_runner.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_bundle.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_capture_template.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_evidence.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_export.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_import.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_operator_evidence_cli.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_operator_runbook.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_promotion.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_real_evidence_intake.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_renderer.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_sample_fixture.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_workflow.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_coverage.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_observability.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_strict_readiness.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/policy_boundary_response.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/policy_boundary_uniformity.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/regression_scenario_packs.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/regression_suite_governance.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_ownership_ledger.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `scripts/qwen_browser_batch_cli_adapter.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `scripts/qwen_ec4b_frontdoor_emission_mapping.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `scripts/qwen_enterprise_cleanup_gate.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `scripts/qwen_final_answer_emission_dry_run.py` | `version_or_archive_by_governance_policy_after_review` |
| `??` | `scripts/qwen_manual_uat_operator_evidence_import.py` | `version_or_archive_by_governance_policy_after_review` |

### pre_existing_ai_changes (60)

| Status | Path | Recommendation |
|---|---|---|
| ` M` | `experimental/qwen_agent_runtime/app/erp_business_reasoning_engine.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `experimental/qwen_agent_runtime/app/semantic_business_understanding_engine.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_clarification_registry.json` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/03_config/qwen_enterprise_metadata/frontdoor_intent_registry.json` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/data_fixes.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/assistant_formatting.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/boundary_support.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_reasoning_policy.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_resolution.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_translation.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/grounded_context.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/customer_lifecycle_support.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/erp_metadata_discovery.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_adapters.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_intent_gate.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_report_executor.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/knowledge_boundary.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_context_graph.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_contracts.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_decision.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_quality_standard.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_request_classification.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_response_renderer.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_runtime.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_schema_hardening.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_validation.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/scope_support.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_boundary_language.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_frame_stack.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_aging_artifact_row_order.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_clarification_resolution_contracts.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_compiled_support_contracts.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_composite_evidence_support.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_financial_statement_followup_clarification_contracts.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_grounded_turn_contracts.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_knowledge_boundary_contracts.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_arbitration.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_context_graph.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_contracts.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_decision.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_evaluation_harness.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_quality_standard.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_response_renderer.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_runtime.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_schema_hardening.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_service_activation.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_validation.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_semantic_financial_resolution.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_ux_s6o_decision_boundary_contracts.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_conversation_regression.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_followup_activation.py` | `separate_ai_change_stream_owner_review_required` |
| ` M` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_trace_inspection.py` | `separate_ai_change_stream_owner_review_required` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_assistant_formatting.py` | `separate_ai_change_stream_owner_review_required` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_enterprise_cleanup_gate_report_contracts.py` | `separate_ai_change_stream_owner_review_required` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_presentation_transform.py` | `separate_ai_change_stream_owner_review_required` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_scope_support_reasoning_arbitration.py` | `separate_ai_change_stream_owner_review_required` |

### unrelated_erp_ui_changes (39)

| Status | Path | Recommendation |
|---|---|---|
| ` M` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/api.py` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| ` M` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/boot.py` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| ` M` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| ` M` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/hooks.py` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| ` M` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/public/css/erp_workspace_ui.css` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| ` M` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/public/js/erp_workspace_ui_boot.js` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| ` M` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/public/js/sales_order_form.js` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| ` M` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/sales_console/service.py` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_home/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_item/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_po_follow_up/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_purchase_order_form/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_purchase_request_form/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_purchase_request_review/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_report/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_rfq_form/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_rfq_review/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_supplier/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_supplier_quotation_form/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_supplier_quotation_review/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/procurement_console_worklist/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/sales_console_home/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/sales_console_report/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/sales_console_worklist/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/procurement_console/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/public/js/delivery_note_form.js` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/public/js/procurement_console/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/public/js/quotation_form.js` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/public/js/runtime/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/public/js/sales_invoice_form.js` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/sales_console/report.py` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/sales_console/worklist.py` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/workspace_governance_manifest.py` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/workspace_governance_manifest.py` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/workspace_registry.py` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |
| `??` | `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/` | `exclude_from_ai_assistant_ec_bundle_separate_owner_stream` |

### seed_data_scripts (25)

| Status | Path | Recommendation |
|---|---|---|
| `??` | `impl_factory/00_governance/archive_docs/dummy_data_working_history_2026-04-15/` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `impl_factory/00_governance/dummy_data/` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `impl_factory/02_seed_data/canonical_2025_04_to_current/` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/build_month1_skeleton_files.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/build_month_workbook_skeleton.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/build_phase12z_master_seed.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/generate_month1_templates.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/generate_opening_documents_draft.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/generate_opening_import_templates.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/populate_month1_procurement_pipeline.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/populate_month1_returns_and_exceptions.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/populate_month1_sales_pipeline.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/populate_month2_procurement_pipeline.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/populate_month2_returns_and_exceptions.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/populate_month2_sales_pipeline.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/populate_month3_procurement_pipeline.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/populate_month3_returns_and_exceptions.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/populate_month3_sales_pipeline.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/populate_q1_finance_layer.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/run_month1_dry_run.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/run_month_dry_run.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/run_opening_documents_dry_run.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/run_phase12aa_master_seed_dry_run.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/validate_opening_layer_controls.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |
| `??` | `scripts/validate_q1_finance_layer.py` | `exclude_from_ec4_bundle_owner_decision_for_seed_package` |

### temp_cache_probe_files (24)

| Status | Path | Recommendation |
|---|---|---|
| `??` | `.codex` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `.codex_tmp/` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `.qwen/` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `_codex_backups/` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/live_artifact_shape_probe.py` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/live_consultant_matrix_probe.py` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/live_consultant_probe_debug.py` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/live_first_more_probe.py` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/live_ux_s5b_reasoning_probe.py` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tmp_live_consultant_probe.py` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp/` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_address_validation/` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_delivery_note_details.png` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_delivery_note_details_after.png` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_delivery_note_details_final.png` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_delivery_note_details_redesign.png` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_delivery_note_details_redesign2.png` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_delivery_note_review/` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_delivery_note_width_check.png` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_delivery_note_width_check2.png` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_delivery_note_width_check3.png` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_delivery_note_width_check_after_fix.png` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_diag/` | `ignore_or_remove_candidate_after_owner_approval_only` |
| `??` | `tmp_live_consultant_probe.py` | `ignore_or_remove_candidate_after_owner_approval_only` |

### unknown_review_required_files (5)

| Status | Path | Recommendation |
|---|---|---|
| ` M` | `impl_factory/00_governance/current_docs/README.md` | `owner_decision_required_before_packaging` |
| `??` | `impl_factory/00_governance/current_docs/primeaxis_business_notes_for_future_ai_discussions_2026-04-17.md` | `owner_decision_required_before_packaging` |
| `??` | `impl_factory/00_governance/current_docs/primeaxis_business_strategy_master_plan_2026-04-05.md` | `owner_decision_required_before_packaging` |
| `??` | `impl_factory/00_governance/current_docs/primeaxis_ui_program/` | `owner_decision_required_before_packaging` |
| `??` | `impl_factory/00_governance/current_docs/primeaxis_v1_parallel_execution_miniphase_plan_2026-04-12.md` | `owner_decision_required_before_packaging` |

## EC-5B Questions

- What is the minimal EC-4 closure source bundle?
- Which tests belong with EC-4?
- Which generated evidence stays in repo versus archive?
- Which governance docs remain in current_docs?
- Which unrelated UI and seed/data changes must be excluded?
- Which temp/probe/cache files can be safely ignored or removed?
- Which files require explicit owner decision?

## Exit Statement

EC-5A is ready for Counterpart review. No packaging or cleanup action should start until Counterpart accepts this baseline and approves EC-5B planning.
