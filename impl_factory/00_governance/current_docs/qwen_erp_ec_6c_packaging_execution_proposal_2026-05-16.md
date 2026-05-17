# EC-6C Packaging Execution Proposal

## Executive Decision

Recommendation:

`ec_6c_packaging_execution_proposal_ready_for_counterpart_review`

EC-6C is a proposal only. It defines the exact future packaging procedure for the AI Assistant S7/EC stabilization bundle, using the merged EC-6B plus EC-6B-A package boundary. It performs no staging, commit, cleanup, delete, move, archive, `.gitignore` change, runtime behavior change, ERP UI work, UX work, Filter work, MI work, family expansion, model-role strict enforcement, or broad `service.py` refactor.

## Baseline

- Branch: `feature/ai-assistant`
- Head: `154be1e`
- Pre-EC-6C dirty count: `317`
- Expected dirty count after adding this EC-6C proposal: `318`
- Boundary source: merged `EC-6B + EC-6B-A`
- Important control condition: do not use the stale EC-6B “not allowed” list by itself. EC-6B-A promotes required dependencies including `contracts.py`.

## Non-Goals

- No staging in EC-6C.
- No commit in EC-6C.
- No cleanup, delete, move, archive, or `.gitignore` edit.
- No ERP UI work.
- No seed/data work.
- No temp/probe/cache cleanup.
- No UX, Filter, MI, or family expansion.
- No model-role strict enforcement.
- No broad `service.py` refactor.

## Merged Final Package Boundary

The package boundary has four approved groups:

- Full-file new EC/S7 source candidates.
- Hunk-aware modified runtime and dependency candidates.
- Full-file test candidates.
- Exact governance and generated evidence candidates.

Any dirty file not named in these groups remains excluded or separate.

## Full-File Source Candidates

These files are new S7/EC source artifacts and are proposed as full-file staging candidates in a future approved packaging step.

### EC-4 Authority Core And Mapping Source

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support_emission_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/enterprise_cleanup_gate_report.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_emission_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_emission_closure_checkpoint.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_emission_dry_run.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_emission_leakage_audit.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_remaining_append_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_emission_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/legacy_runtime_emission_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/nbu_governed_requery_emission_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/reasoning_lane_emission_mapping.py`

### S7 Manual UAT And Evidence Infrastructure Source

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_archive.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_browser_batch_cli.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_browser_batch_runner.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_bundle.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_capture_template.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_evidence.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_export.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_import.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_operator_evidence_cli.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_operator_runbook.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_promotion.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_real_evidence_intake.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_renderer.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_sample_fixture.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/manual_uat_workflow.py`

### Shared S7/EC Governance Source

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_coverage.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_observability.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_strict_readiness.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/policy_boundary_response.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/policy_boundary_uniformity.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/regression_scenario_packs.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/regression_suite_governance.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_ownership_ledger.py`

### S7/EC Support Scripts

- `scripts/qwen_browser_batch_cli_adapter.py`
- `scripts/qwen_ec4b_frontdoor_emission_mapping.py`
- `scripts/qwen_enterprise_cleanup_gate.py`
- `scripts/qwen_final_answer_emission_dry_run.py`
- `scripts/qwen_manual_uat_operator_evidence_import.py`

## Hunk-Aware Source Candidates

These files are modified in the worktree. Future packaging must use hunk-aware review/staging. Do not whole-file stage these files unless the specific exception below is accepted by Counterpart/QA.

### EC-4 Runtime Migration Hunks

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/runtime_gate_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/local_followup_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py` - EC-6D-A required hunk-aware EC-4T1 exception for `nbu_presentation_safe_response`; only the authorized-emission import and safe-response helper hunk are package-allowed.
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recovery_guidance_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

Hunk-aware warning: `service.py` must never be whole-file staged for this package. Only the approved EC-4R2-A, EC-4S2, and EC-4T2 helper/control hunks may be staged after EC-6D approval.

### Shared S7/EC Authority Infrastructure Hunks

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_trace_inspection.py`

These are approved by EC-6A as shared S7/EC authority infrastructure, not EC-4-only emission migration.

### Promoted Dependency Hunks From EC-6B-A

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_frame_stack.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_context_graph.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_request_classification.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_boundary_language.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/knowledge_boundary.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/boundary_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_resolution.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_translation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_intent_gate.py`

Hunk-aware warning: `boundary_support.py` and `frontdoor_intent_gate.py` must not be whole-file staged without explicit Counterpart/QA approval. They are allowed because of dependency closure, but their broad/pre-existing hunks still require review.

### Whole-File Exception Candidate

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py`

This root duplicate was converted to a compatibility facade in EC-4U. It may be whole-file staged only if Counterpart/QA accepts that the full-file replacement is the duplicate-closure artifact. Otherwise use hunk-aware staging.

## Full-File Test Candidates

### EC-4 Direct Emission-Authority Tests

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_artifact_boundary_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_compiled_support_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_control_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_followup_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_local_followup_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_nbu_governed_requery_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_runtime_gate_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_control_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_policy_boundary_authorized_emission_contracts.py`

### EC-4 Mapping, Leakage, And Closure Tests

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_compiled_support_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_followup_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_closure_checkpoint_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_dry_run_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_leakage_audit_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_remaining_append_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_nbu_governed_requery_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_reasoning_lane_emission_mapping_contracts.py`

### S7 Manual UAT Tests

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_archive_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_browser_batch_cli_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_browser_batch_runner_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_bundle_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_capture_template_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_evidence_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_export_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_import_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_operator_capture_template_promotion_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_operator_evidence_cli_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_operator_runbook_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_promotion_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_real_evidence_intake_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_renderer_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_sample_fixture_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_workflow_contracts.py`

### Shared S7/EC Authority Tests

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_authority_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_coverage_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_observability_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_strict_readiness_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_policy_boundary_response_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_policy_boundary_uniformity_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_regression_scenario_packs.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_regression_suite_governance_contracts.py`

## Governance Docs Proposed For Packaging

- `impl_factory/00_governance/current_docs/qwen_erp_ec_4_final_answer_emission_authority_closure_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5a_release_packaging_worktree_control_baseline_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5b_release_packaging_plan_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5c_release_bundle_dry_run_manifest_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5d_mixed_runtime_hunk_level_audit_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5d_a_mapping_evidence_refresh_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5e_final_packaging_decision_gate_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_6a_shared_ai_authority_hunk_resolution_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_6b_ai_packaging_readiness_manifest_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_6b_a_ai_package_dependency_closure_correction_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_6c_packaging_execution_proposal_2026-05-16.md`

## Generated Evidence Proposed For Packaging

Package exact files only. Do not stage the whole `generated/` directory.

- `impl_factory/00_governance/current_docs/generated/ec_3_final_answer_hard_gate_dry_run/qwen_ec3_final_answer_emission_dry_run_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_3_final_answer_hard_gate_dry_run/qwen_ec3_final_answer_emission_dry_run_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4b_frontdoor_emission_mapping/qwen_ec4b_frontdoor_emission_mapping_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4b_frontdoor_emission_mapping/qwen_ec4b_frontdoor_emission_mapping_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4d_compiled_support_emission_mapping/qwen_ec4d_compiled_support_emission_mapping_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4d_compiled_support_emission_mapping/qwen_ec4d_compiled_support_emission_mapping_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4g_reasoning_lane_authorized_emission_migration/qwen_ec4g_reasoning_lane_authorized_emission_migration_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4g_reasoning_lane_authorized_emission_migration/qwen_ec4g_reasoning_lane_authorized_emission_migration_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4h_legacy_runtime_emission_mapping/qwen_ec4h_legacy_runtime_emission_mapping_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4h_legacy_runtime_emission_mapping/qwen_ec4h_legacy_runtime_emission_mapping_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4n_final_answer_emission_leakage_audit/qwen_ec4n_final_answer_emission_leakage_audit_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4n_final_answer_emission_leakage_audit/qwen_ec4n_final_answer_emission_leakage_audit_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4q_a_remaining_append_mapping/qwen_ec4q_a_remaining_append_mapping_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4q_a_remaining_append_mapping/qwen_ec4q_a_remaining_append_mapping_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4u_duplicate_wrapper_visible_context_closure/qwen_ec4u_final_answer_emission_closure_packet.json`
- `impl_factory/00_governance/current_docs/generated/ec_4u_duplicate_wrapper_visible_context_closure/qwen_ec4u_final_answer_emission_closure_packet.md`

Browser/manual evidence should remain QA archive material unless EC-6D explicitly approves it for packaging.

## Files Remaining Excluded Or Separate

These files remain outside the EC-6C proposed package boundary:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/assistant_formatting.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/grounded_context.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/scope_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_adapters.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_report_executor.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_quality_standard.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_response_renderer.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_runtime.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_schema_hardening.py`

Also excluded:

- ERP UI: `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/**`
- seed/data and dummy data streams
- temp/probe/cache files
- PrimeAxis owner-decision docs
- unlisted generated artifacts
- unlisted modified AI files

## Proposed Future Staging Procedure

Do not execute this procedure until EC-6D approves packaging.

1. Capture baseline:
   `git branch --show-current`
   `git rev-parse --short HEAD`
   `git status --short`
2. Stage full-file new EC/S7 source candidates only:
   `git add -- <full-file-source-candidates>`
3. Stage full-file tests only:
   `git add -- <full-file-test-candidates>`
4. Stage governance docs only:
   `git add -- <governance-docs-proposed-for-packaging>`
5. Stage exact generated evidence files only:
   `git add -- <exact-generated-evidence-files>`
6. Hunk-stage modified runtime and dependency files:
   `git add -p -- <hunk-aware-source-candidates>`
7. During hunk staging, reject hunks tied to excluded/separate files, broad service refactor, fresh-query expansion, NBU service activation expansion, UX/Filter/MI/family expansion, ERP UI, seed/data, temp/probe/cache, or owner-decision docs.
8. Review staged boundary:
   `git diff --cached --name-only`
   `git diff --cached --stat`
   `git diff --cached --check`
9. Confirm no excluded files are staged:
   `git diff --cached --name-only | grep -E 'erp_workspace_ui|02_seed_data|dummy_data|tmp|primeaxis|fresh_query_interpreter.py|scope_support.py'`
   Expected result: no output. Run a separate explicit check for `natural_business_understanding_service_activation.py`; it is allowed only as the EC-6D-A hunk-aware EC-4T1 exception and must not be whole-file staged.

## Verification Commands After Future Staging

Run these after any future staging, before commit approval:

```bash
cd /home/deploy/erp-projects/erpai_project1
git diff --cached --check
git diff --cached --name-only
git diff --check -- impl_factory/05_custom_logic/custom_app/ai_assistant_ui
python3 scripts/check_qwen_enterprise_guardrails.py
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_final_answer_authority_contracts \
  ai_assistant_ui.tests.test_authorized_emission_contracts \
  ai_assistant_ui.tests.test_final_answer_emission_closure_checkpoint_contracts \
  ai_assistant_ui.tests.test_final_answer_emission_dry_run_contracts \
  ai_assistant_ui.tests.test_final_answer_emission_leakage_audit_contracts \
  ai_assistant_ui.tests.test_final_answer_remaining_append_mapping_contracts
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_visible_context_followup_activation \
  ai_assistant_ui.tests.test_visible_context_trace_inspection \
  ai_assistant_ui.tests.test_visible_context_conversation_regression
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest discover \
  -s impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests \
  -p 'test_natural_business_understanding_*.py'
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest discover \
  -s impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests \
  -p 'test_manual_uat*.py'
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_semantic_financial_resolution
```

Expected source-scan assertion:

- `active_runtime_direct_assistant_append_count=0`
- `inventory_count=1`
- `migrated_authorized_paths` length `27`

## EC-6C Verification Results

- Dirty count after EC-6C proposal: `318`
- Guardrail: `PASS`
- Scoped AI diff check: `PASS`
- Source scan using `build_final_answer_emission_dry_run_report(reviewer="codex_ec6c_source_scan", status_count=318)`: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths` length `27`
- Final-authority / emission tests: `47 passed`
- Visible-context suite: `90 passed`
- NBU suite: `159 passed`
- Semantic financial suite: `276 passed`

## Final Recommendation

`ec_6c_packaging_execution_proposal_ready_for_counterpart_review`

EC-6C is ready for Counterpart/QA review if verification passes. It does not execute packaging.
