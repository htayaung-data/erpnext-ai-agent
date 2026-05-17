# EC-6B AI Packaging Readiness Manifest

Status update: this EC-6B manifest must be read together with `qwen_erp_ec_6b_a_ai_package_dependency_closure_correction_2026-05-16.md`. EC-6B alone is not dependency-closed because several allowed files depend on dirty support modules that EC-6B originally placed in the owner-decision bucket.

## Executive Decision

Recommendation:

`ec_6b_ai_packaging_readiness_manifest_ready_for_counterpart_review`

EC-6B is a packaging-readiness manifest only. It identifies the exact AI Assistant files that may enter an S7/EC stabilization package after Counterpart/owner approval, and it explicitly excludes unrelated streams. It performs no staging, commit, cleanup, delete, move, archive, `.gitignore` change, runtime behavior change, ERP UI work, UX work, Filter work, MI work, family expansion, model-role strict enforcement, or broad `service.py` refactor.

## Baseline

- Branch: `feature/ai-assistant`
- Head: `154be1e`
- Pre-EC-6B dirty count: `315`
- Expected dirty count after adding this EC-6B manifest: `316`
- EC-4 source-of-truth evidence dirty count: `307`
- EC-6A pre-note dirty count: `314`
- EC-6A post-note dirty count: `315`
- EC-6B scope: documentation/reporting only

The `307 -> 316` difference is expected to be governance documentation only: EC-4 final closure, EC-5A through EC-5E, EC-6A, and this EC-6B manifest. It is not a runtime/test behavior change.

## Scope Guard

Forbidden in EC-6B:

- `no staging`
- `no commit`
- `no cleanup`
- `no delete`
- `no move`
- `no archive`
- `no .gitignore edit`
- `no runtime behavior change`
- `no source implementation`
- `no ERP UI work`
- `no seed/data work`
- `no temp/probe/cache cleanup`
- `no UX, Filter, MI, or family expansion`
- `no model-role strict enforcement`
- `no broad service.py refactor`

## Package Boundary Rule

Only files named in this manifest are eligible for the AI Assistant stabilization package. Any dirty AI file not listed here remains outside the EC-6B allowed package boundary until a separate owner-approved package decision adds it.

## Allowed AI Source Files

### EC-4 Authority Core And Mapping Source

These files are allowed as EC-4 final-answer authority hardening source candidates.

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

### EC-4 Runtime Migration Files

These files are allowed only as hunk-aware EC-4 runtime migration candidates. Whole-file staging remains unsafe unless EC-5D/EC-6A ownership decisions and owner review approve it.

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
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recovery_guidance_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

### Shared S7/EC AI Authority Infrastructure

EC-6A resolved these previously owner-review hunks as shared S7/EC AI authority infrastructure. They are allowed in the shared authority bundle, not as EC-4-only migration files.

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_trace_inspection.py`

### S7 Manual UAT And Evidence Infrastructure Source

These files are allowed as S7/EC evidence-pipeline source candidates. They are not EC-4 emission migration files.

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

### S7 Authority, Policy, Model-Role, And Regression Infrastructure Source

These files are allowed as shared S7/EC governance/runtime support source candidates.

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_coverage.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_observability.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_strict_readiness.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/policy_boundary_response.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/policy_boundary_uniformity.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/regression_scenario_packs.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/regression_suite_governance.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_ownership_ledger.py`

### S7/EC Support Scripts

These scripts are allowed as S7/EC evidence or gate execution support candidates.

- `scripts/qwen_browser_batch_cli_adapter.py`
- `scripts/qwen_ec4b_frontdoor_emission_mapping.py`
- `scripts/qwen_enterprise_cleanup_gate.py`
- `scripts/qwen_final_answer_emission_dry_run.py`
- `scripts/qwen_manual_uat_operator_evidence_import.py`

## AI Source Files Not Allowed Without Separate Owner Decision

The following dirty AI files are not part of the EC-6B allowed package boundary. They may be valid work, but they require a separate owner-approved package decision because EC-6B is not a broad AI cleanup or feature bundle.

- `experimental/qwen_agent_runtime/app/erp_business_reasoning_engine.py`
- `experimental/qwen_agent_runtime/app/semantic_business_understanding_engine.py`
- `impl_factory/03_config/qwen_enterprise_metadata/financial_summary_clarification_registry.json`
- `impl_factory/03_config/qwen_enterprise_metadata/frontdoor_intent_registry.json`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/data_fixes.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/assistant_formatting.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/boundary_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_reasoning_policy.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_resolution.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_translation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/grounded_context.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/customer_lifecycle_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/erp_metadata_discovery.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_adapters.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_intent_gate.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_report_executor.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/knowledge_boundary.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_context_graph.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_decision.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_quality_standard.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_request_classification.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_response_renderer.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_runtime.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_schema_hardening.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_validation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/scope_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_boundary_language.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_frame_stack.py`

## Allowed AI Test Files

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

### Verification-Only Suites For EC-6B

These are required verification coverage for this manifest, but EC-6B does not automatically approve every modified file in these suites for packaging.

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_followup_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_trace_inspection.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_conversation_regression.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_semantic_financial_resolution.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_*.py`

## Governance Docs To Include

### EC Closure And Packaging Docs

- `impl_factory/00_governance/current_docs/qwen_erp_ec_4_final_answer_emission_authority_closure_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5a_release_packaging_worktree_control_baseline_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5b_release_packaging_plan_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5c_release_bundle_dry_run_manifest_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5d_mixed_runtime_hunk_level_audit_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5d_a_mapping_evidence_refresh_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_5e_final_packaging_decision_gate_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_6a_shared_ai_authority_hunk_resolution_2026-05-16.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_6b_ai_packaging_readiness_manifest_2026-05-16.md`

### S7 Closure Docs

S7 docs remain authoritative stabilization history but should not be blindly staged as part of EC-6B. Include only if the final package scope is S7+EC combined and owner approves the historical closure packet.

- `impl_factory/00_governance/current_docs/qwen_erp_s7_x1_release_baseline_file_manifest_2026-05-14.md`
- `impl_factory/00_governance/current_docs/qwen_erp_s7_x2_uat_pipeline_ownership_map_2026-05-14.md`
- `impl_factory/00_governance/current_docs/qwen_erp_s7_x3_scenario_evidence_closure_table_2026-05-14.md`
- `impl_factory/00_governance/current_docs/qwen_erp_s7_x4_final_answer_authority_closure_proof_2026-05-14.md`
- `impl_factory/00_governance/current_docs/qwen_erp_s7_x5_model_role_regression_boundary_closure_report_2026-05-14.md`
- `impl_factory/00_governance/current_docs/qwen_erp_s7_x6_enterprise_stabilization_closure_note_2026-05-14.md`

## Generated Evidence Policy

### Include As Source-Of-Truth EC-4 Evidence

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

### Include As QA Evidence Archive Candidates, Not Release Source

- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_ec1_operator_capture_product_projection_qty_preserves_revenue.json`
- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_s7_browser_batch_cli_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_s7_browser_batch_cli_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_s7_browser_batch_resilience_runner_contract.json`
- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_s7_browser_batch_resilience_runner_contract.md`
- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_s7_manual_uat_promotion_ready_bundle.json`
- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_s7_manual_uat_promotion_ready_bundle.md`
- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_s7_manual_uat_real_evidence_intake.json`
- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_s7_manual_uat_real_evidence_promotion_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_s7_manual_uat_real_evidence_promotion_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_s7_operator_evidence_import_cli_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence/qwen_s7_operator_evidence_import_cli_report.md`
- `impl_factory/00_governance/current_docs/generated/s7_6s_multi_scenario_browser_uat_batch/qwen_s7_6s_operator_capture_multi_scenario_browser_batch.json`
- `impl_factory/00_governance/current_docs/generated/s7_6s_multi_scenario_browser_uat_batch/qwen_s7_manual_uat_promotion_ready_bundle.json`
- `impl_factory/00_governance/current_docs/generated/s7_6s_multi_scenario_browser_uat_batch/qwen_s7_manual_uat_promotion_ready_bundle.md`
- `impl_factory/00_governance/current_docs/generated/s7_6s_multi_scenario_browser_uat_batch/qwen_s7_manual_uat_real_evidence_intake.json`
- `impl_factory/00_governance/current_docs/generated/s7_6s_multi_scenario_browser_uat_batch/qwen_s7_manual_uat_real_evidence_promotion_report.json`
- `impl_factory/00_governance/current_docs/generated/s7_6s_multi_scenario_browser_uat_batch/qwen_s7_manual_uat_real_evidence_promotion_report.md`
- `impl_factory/00_governance/current_docs/generated/s7_6s_multi_scenario_browser_uat_batch/qwen_s7_operator_evidence_import_cli_report.json`
- `impl_factory/00_governance/current_docs/generated/s7_6s_multi_scenario_browser_uat_batch/qwen_s7_operator_evidence_import_cli_report.md`

### Exclude From EC-6B Source Package

Do not package the whole `impl_factory/00_governance/current_docs/generated/` tree. Exclude every generated artifact not explicitly listed above, including these known non-source or superseded paths:

- `impl_factory/00_governance/current_docs/generated/ec_3_final_answer_emission_dry_run/`
- `impl_factory/00_governance/current_docs/generated/ec_2_enterprise_cleanup_gate/`
- `impl_factory/00_governance/current_docs/generated/ec_4f_reasoning_lane_emission_mapping/`
- `impl_factory/00_governance/current_docs/generated/ec_4j_nbu_governed_requery_emission_mapping/`
- `impl_factory/00_governance/current_docs/generated/ec_4l_entity_followup_emission_mapping/`
- `impl_factory/00_governance/current_docs/generated/ec_4p_final_answer_emission_closure_checkpoint/`
- `impl_factory/00_governance/current_docs/generated/s7_6r_real_browser_uat_trial/`
- `impl_factory/00_governance/current_docs/generated/s7_6u_cli_smoke/`
- root-level historical `qwen_s7_*` generated files not listed as QA archive candidates

## Explicit Exclusions

These streams are outside the EC-6B AI package boundary:

- ERP UI: `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/**`
- seed/data scripts: `scripts/build_*`, `scripts/generate_*`, `scripts/populate_*`, `scripts/run_month*`, `scripts/validate_*`, and `impl_factory/02_seed_data/**`
- dummy data: `impl_factory/00_governance/dummy_data/**`
- temp/probe/cache files: `.codex`, `.codex_tmp/**`, `.qwen/**`, `_codex_backups/**`, `tmp/**`, `tmp_*`, `tmp_address_validation/**`, `tmp_diag/**`, `tmp_live_consultant_probe.py`, `live_*_probe.py`
- owner-decision PrimeAxis docs: `primeaxis_business_notes_for_future_ai_discussions_2026-04-17.md`, `primeaxis_business_strategy_master_plan_2026-04-05.md`, `primeaxis_ui_program/**`, `primeaxis_v1_parallel_execution_miniphase_plan_2026-04-12.md`
- unrelated current-docs `README.md` until owner decision
- broad `service.py` refactor beyond EC-4 approved hunks
- model-role strict enforcement implementation
- UX, Filter, MI, and family expansion work

## Packaging Groups

| Group | Status | Packaging implication |
|---|---|---|
| EC-4 authority core/mapping source | allowed candidate | package as EC-4 authority source after review |
| EC-4 runtime migration files | allowed hunk-aware candidate | do not whole-file stage without owner approval |
| shared S7/EC authority infrastructure | allowed shared bundle candidate | package with S7/EC authority docs/tests |
| manual UAT source/tests | allowed S7 evidence-pipeline candidate | package as evidence infrastructure, not EC-4-only |
| model-role/policy/regression source/tests | allowed shared governance candidate | package as shared governance infrastructure |
| selected EC-4 generated evidence | include as source-of-truth evidence | package exact files only |
| EC-1/S7-6S browser evidence | include as QA archive candidates | archive evidence separately from source |
| unlisted generated artifacts | excluded | archive later only with owner approval |
| ERP UI/seed/temp/PrimeAxis docs | excluded | do not include in AI Assistant package |
| pre-existing/unlisted AI changes | owner decision required | not allowed by EC-6B alone |

## Required Verification Results

- `git branch --show-current`: `feature/ai-assistant`
- `git rev-parse --short HEAD`: `154be1e`
- `git status --short` count after EC-6B manifest: `316`
- scoped `git diff --check -- impl_factory/05_custom_logic/custom_app/ai_assistant_ui`: `PASS`
- `python3 scripts/check_qwen_enterprise_guardrails.py`: `PASS`
- visible-context required suite: `90 passed`
- NBU discovery suite: `159 passed`
- semantic financial suite: `276 passed`
- source scan using `build_final_answer_emission_dry_run_report(reviewer="codex_ec6b_source_scan", status_count=316)`: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths` length `27`

The post-manifest dirty count is exactly one higher than the EC-6A accepted state. The delta is this EC-6B governance note only.

## Final Recommendation

`ec_6b_ai_packaging_readiness_manifest_ready_for_counterpart_review`

EC-6B does not approve staging. It defines the AI Assistant package boundary and keeps unrelated ERP UI, seed/data, temp/probe/cache, PrimeAxis docs, and unapproved pre-existing AI changes out of the stabilization package.
