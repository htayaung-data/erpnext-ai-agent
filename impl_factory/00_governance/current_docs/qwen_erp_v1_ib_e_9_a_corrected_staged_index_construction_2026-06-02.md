# V1-IB-E-9-A Corrected Staged Index Construction

Decision target: `v1_ib_e_9_a_corrected_staged_index_construction_ready_for_counterpart_review`

## Scope And Boundary

E-9-A constructed the staged index in `/tmp/erpai_v1_ib_package_readiness_clean` on branch `codex/v1-ib-package-readiness`, HEAD `08f0ec2`, using the corrected E-9-A allowlist and deletion list.

No source files, test files, package config, or runtime behavior were edited in E-9-A. No `/tmp/erpai_pr5_postmerge_verify` files were modified. No branch was created or switched. No commit, push, package build, browser/API UAT, deployment, strict enforcement, package readiness claim, release readiness claim, enterprise/product closure, or V2 work occurred.

## Corrected Deletion Path

The corrected V1-R-G deletion path was used and matched `git status --short` exactly:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_g_synthetic_dataset_manifest_creation_approval_request_2026-05-24.md`

The incorrect path missing `dataset` was not used.

## Pre-Staging Verification

| Check | Result |
| --- | --- |
| Branch | PASS: `codex/v1-ib-package-readiness` |
| HEAD | PASS: `08f0ec2` |
| Staged files before staging | PASS: 0 |
| Corrected deletion list exact match | PASS: 14 expected / 14 actual |
| Root `=` absent | PASS |
| Rejected structural classifier source absent | PASS |
| Rejected structural classifier test absent | PASS |
| Rejected 2026-05-28 structural B reports absent | PASS |
| Old direct lexical tests absent | PASS |
| V1-R/Y report count | PASS: 0 |
| Older non-Y V1-R report count | PASS: 0 |
| EC-10-G absent | PASS |
| Runtime rejected structural classifier refs | PASS: `[]` |
| Accepted baseline tests | PASS: 157 tests |
| C-3 service adversarial tests | PASS: 19 tests |
| Focused contract/classifier/runtime/authorized-emission tests | PASS: 147 tests |
| D authority/trace/legacy tests | PASS: 18 tests |
| Python compile | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe import | PASS |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Source/test positive lexical authority claim scan | PASS: 0 |

## Staging Actions Summary

Staging used an explicit generated path list from the approved E-9-A allowlist:

- 6 accepted source/runtime files
- 19 accepted test files
- 85 accepted V1-IB governance reports already present before E-9-A
- 14 approved old V1-R deletion entries
- this E-9-A governance report

No broad repository staging command was used. No denied artifact was staged.

## Exact Staged File List / Name-Status

```text
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_0_a_formal_report_integrity_fix_2026-05-27.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_0_b_two_model_intent_boundary_authority_amendment_2026-05-27.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_0_c_proposal_completeness_constraint_addendum_2026-05-27.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_0_enterprise_intent_boundary_rebuild_architecture_plan_2026-05-27.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_a_validator_authority_hardening_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_b_raw_message_safety_proof_hardening_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_c_unknown_decision_action_fail_closed_hardening_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_contract_schema_validator_clause_model_ontology_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_d_remove_lexical_authority_foundation_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_e_proposal_completeness_independent_parse_guard_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_f_non_self_attestable_mechanical_authority_guard_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_g_independent_clause_role_verification_guard_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_h_external_verifier_evidence_envelope_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_i_trusted_external_verifier_provenance_guard_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_j_validator_owned_safety_proof_authority_gate_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_k_non_derivative_validator_owned_raw_message_safety_proof_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_l_raw_safety_proof_uniqueness_conflict_evidence_integrity_guard_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_m_raw_message_safety_analyzer_contract_evidence_semantics_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_n_evidence_truth_binding_raw_message_analysis_gate_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_o_executed_raw_message_analyzer_authority_no_assertion_only_analysis_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_p_a_replayed_analyzer_semantic_completeness_fix_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_p_b_safe_factual_question_punctuation_replay_fix_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_p_c_durable_sibling_adversarial_replay_test_hardening_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_p_replayed_raw_message_safety_authority_audit_only_provenance_contract_2026-05-28.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_a_q_contract_validator_foundation_closure_gate_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_0_deterministic_classifier_restart_plan_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_1_proposal_classifier_implementation_boundary_request_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_a_proposal_classifier_evidence_strictness_fix_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_b_proposal_classifier_closure_checkpoint_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_proposal_classifier_implementation_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_0_runtime_integration_plan_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_1_runtime_integration_boundary_request_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_2_a_stale_contract_final_emission_authority_fix_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_2_b_legacy_authorized_emission_test_alignment_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_2_c_runtime_integration_closure_checkpoint_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_2_runtime_integration_implementation_2026-05-29.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_0_adversarial_runtime_test_expansion_plan_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_1_first_adversarial_runtime_test_slice_boundary_request_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_2_first_adversarial_runtime_test_implementation_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_3_service_level_adversarial_runtime_boundary_request_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_4_a_stale_visible_context_service_test_hardening_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_4_b_a_visible_context_helper_fail_closed_correction_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_4_b_b_legacy_runtime_integration_test_alignment_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_4_b_stale_visible_context_runtime_authority_fix_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_4_c_service_level_visible_context_report_routing_closure_checkpoint_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_4_service_level_visible_context_report_routing_tests_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_5_0_service_level_model_reasoning_report_selector_trace_boundary_request_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_5_1_service_level_adversarial_test_implementation_boundary_request_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_5_2_service_level_model_reasoning_report_selector_trace_tests_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_5_3_service_level_model_reasoning_report_selector_trace_closure_checkpoint_2026-05-30.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_6_long_context_full_call_stack_service_tests_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_7_adversarial_service_level_phase_closure_readiness_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_4_runtime_integration_closure_v1_ib_d_transition_plan_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_5_runtime_integration_formal_closure_checkpoint_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_0_next_phase_planning_after_runtime_integration_closure_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_1_authority_surface_inventory_call_site_map_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_2_a_current_message_report_routing_authority_fix_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_2_authority_consistency_tests_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_2_b_authority_consistency_closure_checkpoint_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_3_a_blocked_turn_trace_raw_message_redaction_fix_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_3_b_trace_diagnostic_audit_closure_checkpoint_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_3_trace_diagnostic_contract_audit_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_4_a_legacy_restrict_only_assertion_tests_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_4_b_rejected_structural_classifier_quarantine_removal_plan_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_4_c_legacy_lexical_tests_classification_alignment_plan_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_4_d_stale_v1_r_y_z_report_archive_package_exclusion_plan_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_4_e_1_accepted_evidence_manifest_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_4_e_package_readiness_cleanup_plan_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_4_legacy_authority_retirement_quarantine_plan_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_5_formal_closure_readiness_2026-05-31.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_0_clean_branch_package_readiness_boundary_request_2026-06-01.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_1_clean_branch_preparation_plan_2026-06-01.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_2_accepted_artifact_reapply_staging_plan_2026-06-01.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_3_a_older_v1_r_inventory_completeness_fix_2026-06-01.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_3_rejected_historical_artifact_exclusion_plan_2026-06-01.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_4_unknown_equals_file_classification_disposition_plan_2026-06-01.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_5_package_exclusion_verification_plan_2026-06-01.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_6_clean_branch_implementation_boundary_request_2026-06-01.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_7_a_base_branch_historical_v1_r_report_exclusion_fix_2026-06-01.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_7_b_clean_branch_verification_2026-06-01.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_7_c_clean_branch_d_legacy_restrict_only_test_alignment_2026-06-02.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_7_clean_branch_creation_accepted_artifact_reapply_2026-06-01.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_7_d_clean_branch_verification_closure_checkpoint_2026-06-02.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_8_staging_commit_boundary_request_2026-06-02.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_9_a_corrected_staged_index_construction_2026-06-02.md
A	impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_9_staged_index_construction_2026-06-02.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_a_human_like_browser_uat_question_bank_automation_plan_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_b_browser_uat_automation_harness_plan_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_c_controlled_browser_uat_execution_request_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_d_browser_uat_execution_input_preflight_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_e_synthetic_dataset_environment_input_plan_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_f_synthetic_dataset_manifest_template_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_g_synthetic_dataset_manifest_creation_approval_request_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_h_synthetic_manifest_validator_plan_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_i_a_synthetic_manifest_validator_hardening_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_i_b_synthetic_manifest_validator_hardening_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_i_synthetic_manifest_validator_implementation_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_j_synthetic_manifest_creation_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_k_browser_uat_environment_readiness_recheck_2026-05-24.md
D	impl_factory/00_governance/current_docs/qwen_erp_v1_r_p_packaging_readiness_baseline_2026-05-24.md
M	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_contract.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_proposal_classifier.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_runtime_integration.py
M	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/user_intent_boundary.py
M	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_authorized_emission_contracts.py
M	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_control_authorized_emission_contracts.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_authority_surface_consistency.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_cross_lane_contract_identity.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_legacy_restrict_only.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_trace_diagnostic_authority_consistency.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_trace_diagnostic_contract_audit.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_intent_boundary_contract_validator.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_intent_boundary_proposal_classifier.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_adversarial_final_emission.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_adversarial_prerouting.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_final_emission_contract_veto.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_integration.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_long_context_full_stack.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_model_reasoning.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_report_routing.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_report_selector.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_trace_redaction.py
A	impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_visible_context.py
```

## Post-Staging Verification

| Check | Result |
| --- | --- |
| Staged file list matches approved allowlist/deletion list plus E-9-A report | PASS |
| No denied artifact staged | PASS |
| Staged files count | PASS: 125 |
| `git diff --cached --check` | PASS |
| `git diff --check` | PASS |
| Package-exclusion gates | PASS |
| Runtime rejected structural classifier refs | PASS: `[]` |
| Raw append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe import | PASS |
| Report hygiene | PASS after final scan |
| Remaining unstaged dirty files | PASS: 0 |
| Untracked files after staging | PASS: 0 |

## Boundary Statement

E-9-A stops after staged-index verification. No commit, push, package build, browser/API UAT, deployment, strict enforcement, package readiness claim, release readiness claim, enterprise/product closure, or V2 work occurred.

Decision request:

`v1_ib_e_9_a_corrected_staged_index_construction_ready_for_counterpart_review`
