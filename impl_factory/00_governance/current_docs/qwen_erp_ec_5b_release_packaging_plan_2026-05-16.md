# EC-5B Release Packaging Plan

## Executive Decision

Recommendation:

`enterprise_cleanup_ec_5b_ready_for_counterpart_review`

EC-5B is planning only. It proposes packaging boundaries and owner decisions but performs no cleanup, staging, delete, move, commit, `.gitignore` change, or implementation work.

## Baseline

- Branch: `feature/ai-assistant`
- Head: `154be1e`
- Pre-EC-5B dirty count: `309`
- Expected dirty count after adding this EC-5B plan: `310`
- Refined inventory checksum: `0625cb8ae636cf1afb33598d657ebbeee81fc6af94ed00df2e3faf6527e6a41b`
- Checksum method: `sha256` over newline-joined rows formatted as `status<TAB>refined_bucket<TAB>path`, using `git status --short -z` order.
- Generated at UTC: `2026-05-16T03:46:57+00:00`

## Refined Packaging Buckets

| Bucket | Count | Packaging decision |
|---|---:|---|
| `ec4_direct_emission_authority_tests_candidate` | 12 | `candidate_for_minimal_ec4_bundle_after_hunk_review` |
| `ec4_ec5_closure_docs_candidate` | 3 | `candidate_for_minimal_ec4_bundle_after_hunk_review` |
| `ec4_mapping_leakage_closure_tests_candidate` | 10 | `candidate_for_minimal_ec4_bundle_after_hunk_review` |
| `exclude_seed_data_stream` | 25 | `exclude_from_ec_bundle` |
| `exclude_temp_cache_probe` | 24 | `exclude_from_ec_bundle` |
| `exclude_unrelated_erp_ui` | 39 | `exclude_from_ec_bundle` |
| `generated_evidence_policy_required` | 1 | `selected_source_of_truth_only_archive_rest` |
| `historical_s7_ec_governance_docs` | 49 | `review_required` |
| `manual_uat_infrastructure_tests_shared` | 16 | `shared_infrastructure_review_before_bundling` |
| `manual_uat_support_source_shared` | 15 | `shared_infrastructure_review_before_bundling` |
| `mixed_runtime_file_hunk_review_required` | 16 | `review_required` |
| `model_role_support_source_shared` | 3 | `shared_infrastructure_review_before_bundling` |
| `model_role_tests_shared` | 3 | `shared_infrastructure_review_before_bundling` |
| `owner_decision_unknown_docs` | 5 | `review_required` |
| `policy_boundary_support_source_shared` | 2 | `shared_infrastructure_review_before_bundling` |
| `policy_boundary_tests_shared` | 2 | `shared_infrastructure_review_before_bundling` |
| `pre_existing_ai_source_not_ec4_bundle` | 33 | `separate_ai_stream_not_ec4_bundle` |
| `pre_existing_ai_tests_not_ec4_bundle` | 28 | `separate_ai_stream_not_ec4_bundle` |
| `pure_ec4_closure_source_candidate` | 12 | `candidate_for_minimal_ec4_bundle_after_hunk_review` |
| `s7_ec_support_scripts_review_required` | 5 | `review_required` |
| `shared_final_authority_tests_candidate` | 1 | `shared_infrastructure_review_before_bundling` |
| `shared_regression_governance_source` | 3 | `shared_infrastructure_review_before_bundling` |
| `shared_regression_governance_tests` | 2 | `shared_infrastructure_review_before_bundling` |

## Minimal EC-4 Source Bundle Proposal

Candidate pure EC-4 closure source files:
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

Mixed runtime files requiring hunk-level review before packaging:
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
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recovery_guidance_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_trace_inspection.py`

Do not package an entire mixed runtime file as EC-4-owned without hunk-level review. Important mixed examples include `service.py`, `visible_context_followup_activation.py`, NBU activation modules, reasoning/legacy/frontdoor lanes, local follow-up, runtime gate, artifact boundary, compiled support, and trace inspection.

## Minimal EC-4 Test Bundle Proposal

Direct emission-authority tests:
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

Mapping/leakage/closure tests:
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

Shared tests requiring review before inclusion:
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_authority_contracts.py`
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
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_coverage_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_observability_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_strict_readiness_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_policy_boundary_response_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_policy_boundary_uniformity_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_regression_scenario_packs.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_regression_suite_governance_contracts.py`

## Generated Evidence Policy

| Evidence bucket | Count | Policy |
|---|---:|---|
| `historical_ec_evidence` | 16 | `archive historical EC mapping evidence unless needed by reviewer` |
| `historical_s7_evidence` | 31 | `archive historical S7 evidence unless needed by reviewer` |
| `non_source_of_truth_historical_evidence` | 3 | `do not version as source-of-truth; archive only with marker` |
| `qa_traceability_browser_evidence` | 28 | `archive or keep selected browser evidence by QA policy` |
| `source_of_truth_ec4_closure_evidence` | 10 | `keep selected EC-4 closure reports for QA traceability` |

Source-of-truth EC-4 closure evidence candidates:
- `impl_factory/00_governance/current_docs/generated/ec_3_final_answer_hard_gate_dry_run/qwen_ec3_final_answer_emission_dry_run_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_3_final_answer_hard_gate_dry_run/qwen_ec3_final_answer_emission_dry_run_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4b_frontdoor_emission_mapping/qwen_ec4b_frontdoor_emission_mapping_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4b_frontdoor_emission_mapping/qwen_ec4b_frontdoor_emission_mapping_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4n_final_answer_emission_leakage_audit/qwen_ec4n_final_answer_emission_leakage_audit_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4n_final_answer_emission_leakage_audit/qwen_ec4n_final_answer_emission_leakage_audit_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4q_a_remaining_append_mapping/qwen_ec4q_a_remaining_append_mapping_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4q_a_remaining_append_mapping/qwen_ec4q_a_remaining_append_mapping_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4u_duplicate_wrapper_visible_context_closure/qwen_ec4u_final_answer_emission_closure_packet.json`
- `impl_factory/00_governance/current_docs/generated/ec_4u_duplicate_wrapper_visible_context_closure/qwen_ec4u_final_answer_emission_closure_packet.md`

## Governance Docs Policy

- Keep concise final closure notes and accepted baseline/approval notes in `current_docs`.
- Archive intermediate six-fact gates and historical slice notes if they are not needed for release traceability.
- Do not include PrimeAxis business strategy/UI program docs in the EC bundle without owner approval.
- Keep EC-4 final closure note and EC-5A/EC-5B packaging notes as current governance records until packaging is accepted.

## Excluded Streams

- `exclude_unrelated_erp_ui`: `39` entries. Exclude from EC-4 bundle.
- `exclude_seed_data_stream`: `25` entries. Exclude from EC-4 bundle.
- `exclude_temp_cache_probe`: `24` entries. Exclude from EC-4 bundle.

## Owner Decision List

Unknown/review-required docs must not enter any EC bundle until owner decision:
- `impl_factory/00_governance/current_docs/README.md`
- `impl_factory/00_governance/current_docs/primeaxis_business_notes_for_future_ai_discussions_2026-04-17.md`
- `impl_factory/00_governance/current_docs/primeaxis_business_strategy_master_plan_2026-04-05.md`
- `impl_factory/00_governance/current_docs/primeaxis_ui_program/`
- `impl_factory/00_governance/current_docs/primeaxis_v1_parallel_execution_miniphase_plan_2026-04-12.md`

Additional owner decisions required:
- whether generated EC-4 JSON/Markdown reports should be versioned or archived outside source
- whether manual UAT support modules are part of S7/EC shared infrastructure bundle or separate governance bundle
- whether model-role and policy-boundary modules should be packaged with EC-4 or deferred to later model-role cleanup
- whether pre-existing AI/NBU files touched before EC-4 need separate hunk-level packaging
- whether temp/probe/cache files can be removed or ignored in a later approved cleanup slice

## Proposed Safe Cleanup List

No cleanup is approved in EC-5B. Future cleanup candidates after approval:
- remove or ignore local temp/probe/cache files
- archive non-source-of-truth generated reports
- separate ERP UI stream from AI assistant EC bundle
- separate seed/data scripts into their own owner-approved package
- perform hunk-level review for mixed runtime files before any release bundle

## Risks And Blockers

- Mixed runtime files cannot be packaged safely without hunk-level review.
- Generated evidence directory contains both source-of-truth and historical artifacts.
- EC-5A broad categories must not be used directly for staging.
- Unknown PrimeAxis/current_docs files remain owner-decision blockers.
- ERP UI and seed/data streams are unrelated to EC-4 and must stay excluded.

## Non-Goals

- `no staging`
- `no commit`
- `no delete`
- `no move`
- `no .gitignore change`
- `no cleanup`
- `no implementation`
- `no UX, Filter, MI, or family expansion`

## Exit Statement

EC-5B is ready for Counterpart review. No packaging action should start until Counterpart accepts this plan and approves a specific implementation slice.
