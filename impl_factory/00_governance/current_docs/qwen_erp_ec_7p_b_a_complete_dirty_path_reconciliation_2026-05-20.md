# EC-7P-B-A Complete Dirty-Path Reconciliation

Decision: ec_7p_b_a_complete_dirty_path_reconciliation_ready_for_counterpart_review

Date: 2026-05-20
Generated: 2026-05-19T18:44:46+00:00
Branch: feature/ec-7b0-runtime-import-integrity
Head: 2641458
Expanded dirty path count reconciled before this report: `135`
Current expanded dirty count after this report: `136`
Staged files count: `0`
Runtime effect: `none`
Packaging action performed: `none`

## Scope

EC-7P-B-A is a report-only correction to EC-7P-B. It reconciles every pre-report expanded dirty path into an explicit packaging decision. This report itself is an additional governance artifact for Counterpart/QA review. No staging, commit, cleanup, enforcement, runtime behavior work, EC-7H/live UAT work, or deployment was performed.

## Decision Vocabulary

- `bundle_a_include`: EC-7B0 runtime import/dependency integrity bundle candidate.
- `bundle_b_include`: EC-7 metadata/provenance/soft-gate source, focused tests, or summary governance bundle candidate.
- `bundle_c_optional_generated`: generated evidence candidate, included only if QA explicitly approves generated evidence in source.
- `defer_governance_micro_report`: accepted micro-slice report that may be archived/deferred from a minimal package unless full traceability is requested.
- `verification_only_test`: accepted test used to verify the package but not necessarily included in minimal EC-7 metadata package.
- `explicit_exclude`: excluded from EC-7 package unless owner/QA reclassifies.

## Reconciliation Counts

| Decision | Count |
|---|---:|
| `bundle_a_include` | 44 |
| `bundle_b_include` | 51 |
| `bundle_c_optional_generated` | 1 |
| `defer_governance_micro_report` | 19 |
| `verification_only_test` | 16 |
| `explicit_exclude` | 4 |

## Complete Dirty-Path Ledger

| Status | Decision | Path | Rationale |
|---|---|---|---|
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/artifact_narrative.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_system.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/composite_reads.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_intent_gate.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/runtime_gate_lane.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/local_followup_support.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_coverage.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_observability.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_runtime.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/reasoning_execution.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_interpreter.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_reasoning_activation.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_repair_intent.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_trace_inspection.py` | EC-7 metadata/provenance wiring source candidate; hunk-aware review required if broad runtime file. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_artifact_boundary_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_compiled_support_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_control_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_followup_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_emission_mapping_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_local_followup_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_service_activation.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_nbu_governed_requery_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_runtime_gate_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_control_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_policy_boundary_authorized_emission_contracts.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_followup_activation.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| ` M` | `verification_only_test` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_trace_inspection.py` | Accepted authority/regression test used for verification, not necessarily part of minimal EC-7 metadata package. |
| `??` | `explicit_exclude` | `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_cli_report.json` | S7 browser batch generated scratch/evidence is outside EC-7 metadata packaging. |
| `??` | `explicit_exclude` | `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_cli_report.md` | S7 browser batch generated scratch/evidence is outside EC-7 metadata packaging. |
| `??` | `explicit_exclude` | `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_resilience_runner_contract.json` | S7 browser batch generated scratch/evidence is outside EC-7 metadata packaging. |
| `??` | `explicit_exclude` | `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_resilience_runner_contract.md` | S7 browser batch generated scratch/evidence is outside EC-7 metadata packaging. |
| `??` | `bundle_b_include` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7b0_b_runtime_import_integrity_repair_2026-05-17.md` | Accepted EC-7 summary/closure/planning governance report for Bundle B traceability. |
| `??` | `bundle_b_include` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7b_runtime_metadata_coverage_inventory_2026-05-17.md` | Accepted EC-7 summary/closure/planning governance report for Bundle B traceability. |
| `??` | `bundle_b_include` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7c_runtime_metadata_envelope_contract_2026-05-18.md` | Accepted EC-7 summary/closure/planning governance report for Bundle B traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7d_a_deterministic_control_metadata_wiring_2026-05-18.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7d_b_compiled_legacy_metadata_wiring_2026-05-18.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7d_c_artifact_local_followup_metadata_wiring_2026-05-18.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7d_d_entity_service_metadata_wiring_2026-05-18.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7d_e_nbu_visible_context_metadata_wiring_2026-05-18.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `bundle_b_include` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7d_f_deterministic_control_metadata_closure_2026-05-18.md` | Accepted EC-7 summary/closure/planning governance report for Bundle B traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7e_a_ai_runtime_metadata_provenance_inventory_2026-05-18.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7e_b_light_semantic_metadata_wiring_2026-05-18.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7e_c2_0_role_taxonomy_decision_2026-05-19.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7e_c2_1_metadata_contract_taxonomy_extension_2026-05-19.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7e_c2_a_user_visible_helper_metadata_wiring_2026-05-19.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7e_c2_b_report_evidence_helper_metadata_wiring_2026-05-19.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `bundle_b_include` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7e_c2_c1_light_semantic_outcome_strict_readiness_guard_2026-05-19.md` | Accepted EC-7 summary/closure/planning governance report for Bundle B traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7e_c2_c_service_validator_provenance_probes_2026-05-19.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7e_c2_secondary_model_backed_helper_classification_2026-05-18.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7e_c_heavy_reasoning_nbu_shadow_metadata_wiring_2026-05-18.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7f_a_runtime_metadata_probe_plan_2026-05-19.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7f_b_light_semantic_runtime_probes_2026-05-19.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7f_c_heavy_reasoning_nbu_shadow_runtime_probes_2026-05-19.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7f_d_helper_tool_runtime_probes_2026-05-19.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `defer_governance_micro_report` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7f_e_deterministic_control_runtime_probes_2026-05-19.md` | Accepted micro-slice governance report; defer from minimal bundle unless QA requests full traceability. |
| `??` | `bundle_b_include` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md` | Accepted EC-7 summary/closure/planning governance report for Bundle B traceability. |
| `??` | `bundle_b_include` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7g_a_strict_readiness_soft_gate_plan_2026-05-19.md` | Accepted EC-7 summary/closure/planning governance report for Bundle B traceability. |
| `??` | `bundle_c_optional_generated` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.json` | Machine-readable EC-7G-B soft-gate evidence; include only if QA approves generated evidence in source. |
| `??` | `bundle_b_include` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.md` | Accepted EC-7 summary/closure/planning governance report for Bundle B traceability. |
| `??` | `bundle_b_include` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7g_c_soft_gate_evidence_source_classification_2026-05-20.md` | Accepted EC-7 summary/closure/planning governance report for Bundle B traceability. |
| `??` | `bundle_b_include` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7p_a_packaging_readiness_baseline_2026-05-20.md` | Accepted EC-7 summary/closure/planning governance report for Bundle B traceability. |
| `??` | `bundle_b_include` | `impl_factory/00_governance/current_docs/qwen_erp_ec_7p_b_packaging_boundary_dependency_closure_plan_2026-05-20.md` | Accepted EC-7 summary/closure/planning governance report for Bundle B traceability. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/analytical_scope_policy.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/assistant_formatting.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/boundary_contract_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_definition_state.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_rule_registry.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_threshold_state.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/collections_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/composite_artifact_state.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compound_request_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/grounded_context.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/message_history.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/session_context.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/continuation_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/conversation_control_decisions.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/conversation_control_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/conversation_snapshot.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/customer_kpi_runtime_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/customer_lifecycle_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/defaults_repository.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_period_aggregation_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_reference_resolution.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/framework/__init__.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/framework/frappe_defaults_repository.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_composite_runtime_execution.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_execution_registry.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_execution_state.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_runtime_execution.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/compiled_query_lane.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/entity_drilldown_lane.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/repair_lane.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/light_semantic_metadata.py` | EC-7 metadata contract/helper/soft-gate source. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/master_data_frontdoor_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/master_data_lookup_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metric_union_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_backed_helper_metadata.py` | EC-7 metadata contract/helper/soft-gate source. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/ranking_limit_parser.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recent_focus_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recovery_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/requery_message_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/restore_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/rollout.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_message_compilation.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_metadata_contract.py` | EC-7 metadata contract/helper/soft-gate source. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/scope_support.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/strict_readiness_soft_gate.py` | EC-7 metadata contract/helper/soft-gate source. |
| `??` | `bundle_a_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/turn_journal.py` | Restored EC-7B0 runtime import/dependency integrity module. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_deterministic_control_runtime_metadata_probes.py` | Focused EC-7 metadata/probe/soft-gate test required for Bundle B verification. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_governed_tool_runtime_metadata_wiring.py` | Focused EC-7 metadata/probe/soft-gate test required for Bundle B verification. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_heavy_reasoning_nbu_shadow_runtime_probes.py` | Focused EC-7 metadata/probe/soft-gate test required for Bundle B verification. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_heavy_shadow_runtime_metadata_contracts.py` | Focused EC-7 metadata/probe/soft-gate test required for Bundle B verification. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_helper_tool_runtime_probes.py` | Focused EC-7 metadata/probe/soft-gate test required for Bundle B verification. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_light_semantic_runtime_metadata_contracts.py` | Focused EC-7 metadata/probe/soft-gate test required for Bundle B verification. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_light_semantic_runtime_probes.py` | Focused EC-7 metadata/probe/soft-gate test required for Bundle B verification. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_backed_helper_metadata_wiring.py` | Focused EC-7 metadata/probe/soft-gate test required for Bundle B verification. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_runtime_metadata_contract.py` | Focused EC-7 metadata/probe/soft-gate test required for Bundle B verification. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_validator_provenance_probes.py` | Focused EC-7 metadata/probe/soft-gate test required for Bundle B verification. |
| `??` | `bundle_b_include` | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_strict_readiness_soft_gate.py` | Focused EC-7 metadata/probe/soft-gate test required for Bundle B verification. |

## Bundle Boundary Consequences

- Bundle A now explicitly includes all restored EC-7B0 dependency files found in the expanded dirty path set.
- Bundle B now explicitly includes focused EC-7 metadata/probe/soft-gate source and tests, and marks accepted summary governance reports.
- Accepted micro-slice reports are not silently omitted; they are marked `defer_governance_micro_report` for Counterpart/QA traceability policy.
- Existing authorized-emission/regression tests that prove safety but are not EC-7 metadata-specific are marked `verification_only_test`.
- S7 browser batch generated artifacts remain `explicit_exclude` because they are outside EC-7 metadata packaging.

## Remaining Blockers Before EC-7P-C

1. Counterpart/QA must accept this complete ledger and decide whether deferred micro-reports belong in the minimal package or archive.
2. A future EC-7P-C dry-run package must be built from this ledger, not from broad directory staging.
3. Hunk-aware Bundle B files still require staged-index or clean-worktree proof before any package can be accepted.
4. Bundle C generated evidence inclusion remains optional and requires explicit approval.

## Non-Goals

- `no_staging`
- `no_commit`
- `no_cleanup`
- `no_enforcement`
- `no_runtime_behavior_work`
- `no_ec_7h_live_trace_work`
- `no_deployment`

## Final Recommendation

`ec_7p_b_a_complete_dirty_path_reconciliation_ready_for_counterpart_review`
