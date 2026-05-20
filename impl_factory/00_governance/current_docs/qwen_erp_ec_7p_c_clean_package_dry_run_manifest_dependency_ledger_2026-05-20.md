# EC-7P-C Clean Package Dry-Run Manifest / Dependency Ledger

Decision: ec_7p_c_clean_package_dry_run_manifest_ready_for_counterpart_review

Date: 2026-05-20
Generated: 2026-05-19T18:55:36+00:00
Branch: feature/ec-7b0-runtime-import-integrity
Head: 2641458
Input ledger: `qwen_erp_ec_7p_b_a_complete_dirty_path_reconciliation_2026-05-20.md`
Runtime effect: `none`
Staging performed: `false`
Commit/push performed: `false`
Current expanded dirty count after this report: `137`
Staged files count: `0`

## Scope

EC-7P-C is a clean package dry-run manifest only. It does not stage, commit, push, clean, enforce, change runtime behavior, run EC-7H live traces, deploy, or perform UX/Filter/MI/family expansion work.

Because staging is not explicitly approved, this slice does not run cached/staged-index verification. It defines exact future package candidate boundaries from EC-7P-B-A.

## Bundle Decision

Bundle A and Bundle B are proposed for future clean-package construction after Counterpart/QA approval. Bundle C generated JSON is **excluded from the default package** and remains optional; include it only if QA explicitly requests machine-readable generated evidence in source.

## Bundle A: Full-File Include Candidates

These are restored EC-7B0 dependency modules. Future packaging may include them whole-file if dependency closure remains clean from a clean base.

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/analytical_scope_policy.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/assistant_formatting.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/boundary_contract_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_definition_state.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_rule_registry.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_threshold_state.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/collections_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/composite_artifact_state.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compound_request_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/grounded_context.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/message_history.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/session_context.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/continuation_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/conversation_control_decisions.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/conversation_control_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/conversation_snapshot.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/customer_kpi_runtime_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/customer_lifecycle_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/defaults_repository.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_period_aggregation_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_reference_resolution.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/framework/__init__.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/framework/frappe_defaults_repository.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_composite_runtime_execution.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_execution_registry.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_execution_state.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_runtime_execution.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/compiled_query_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/entity_drilldown_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/repair_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/master_data_frontdoor_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/master_data_lookup_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metric_union_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/ranking_limit_parser.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recent_focus_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recovery_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/requery_message_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/restore_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/rollout.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_message_compilation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/scope_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/turn_journal.py`

## Bundle B: Full-File Include Candidates

These are new EC-7 metadata/provenance/soft-gate source files, focused tests, and governance reports that can be included whole-file in a future package attempt.

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_metadata_contract.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/light_semantic_metadata.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_backed_helper_metadata.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/strict_readiness_soft_gate.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_runtime_metadata_contract.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_light_semantic_runtime_metadata_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_light_semantic_runtime_probes.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_heavy_shadow_runtime_metadata_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_heavy_reasoning_nbu_shadow_runtime_probes.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_backed_helper_metadata_wiring.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_governed_tool_runtime_metadata_wiring.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_validator_provenance_probes.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_helper_tool_runtime_probes.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_deterministic_control_runtime_metadata_probes.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_strict_readiness_soft_gate.py`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7b0_b_runtime_import_integrity_repair_2026-05-17.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7b_runtime_metadata_coverage_inventory_2026-05-17.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7c_runtime_metadata_envelope_contract_2026-05-18.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7d_f_deterministic_control_metadata_closure_2026-05-18.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7e_c2_c1_light_semantic_outcome_strict_readiness_guard_2026-05-19.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7g_a_strict_readiness_soft_gate_plan_2026-05-19.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7g_c_soft_gate_evidence_source_classification_2026-05-20.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7p_a_packaging_readiness_baseline_2026-05-20.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7p_b_packaging_boundary_dependency_closure_plan_2026-05-20.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7p_b_a_complete_dirty_path_reconciliation_2026-05-20.md`
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7p_c_clean_package_dry_run_manifest_dependency_ledger_2026-05-20.md`

## Bundle B: Hunk-Aware Include Candidates

| File | Future hunk rule |
|---|---|
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/artifact_narrative.py` | EC-7E-C2-A helper provenance envelope wiring only; exclude unrelated narrative behavior hunks if present. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_system.py` | EC-7E-C2-A helper provenance envelope wiring only; preserve clarification text/control behavior. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support.py` | EC-7D-B deterministic/control metadata envelope wiring only; preserve answer and authority behavior. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/composite_reads.py` | EC-7E-C2-B governed-tool runtime metadata only; preserve composite/report selection behavior. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py` | EC-7D-D entity follow-up deterministic/error metadata only; preserve entity-detail behavior. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py` | EC-7E-B/C2-B fresh query semantic and compiled-read provenance hunks only; hunk-aware required. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_intent_gate.py` | EC-7E-B frontdoor semantic metadata hunks only; hunk-aware required. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py` | EC-7D-C artifact boundary metadata hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py` | EC-7D-A clarification/control metadata hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py` | EC-7D-B legacy deterministic/policy/error metadata hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py` | EC-7E-C reasoning metadata surface hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/runtime_gate_lane.py` | EC-7D-A runtime gate policy metadata hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/local_followup_support.py` | EC-7D-C local follow-up deterministic visible-context metadata hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_coverage.py` | EC-7 metadata coverage/soft-readiness helper hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_observability.py` | EC-7 model-role observability helper hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py` | EC-7D-E NBU governed requery metadata hunks only; hunk-aware required. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_runtime.py` | EC-7E-C NBU shadow observer metadata hunks only; hunk-aware required. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py` | EC-7D-E NBU safe/control metadata hunks only; hunk-aware required. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/reasoning_execution.py` | EC-7E-C heavy reasoning runtime provenance hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_interpreter.py` | EC-7E-B/C2-C1 light semantic metadata/status guard hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_reasoning_activation.py` | EC-7E-B semantic reasoning activation metadata hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_repair_intent.py` | EC-7E-B semantic repair intent metadata hunks only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | EC-7B0 import integrity plus EC-7D-D service policy/control metadata hunks only; hunk-aware required, never whole-file. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py` | EC-7D-E visible-context metadata consistency hunks only; hunk-aware required. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_trace_inspection.py` | EC-7D-E trace/control metadata hunks only; hunk-aware required. |

## Bundle C: Generated Evidence Decision

- Default decision: `exclude_from_default_package`.
- Optional generated evidence candidate: `impl_factory/00_governance/current_docs/qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.json`.
- Rationale: Markdown governance reports are the default source-of-truth; generated JSON should enter source only if QA explicitly requests machine-readable evidence.

## Deferred / Verification-Only Paths

### Verification-Only Tests

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_artifact_boundary_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_compiled_support_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_control_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_followup_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_local_followup_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_natural_business_understanding_service_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_nbu_governed_requery_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_runtime_gate_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_control_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_policy_boundary_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_followup_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_trace_inspection.py`

These tests should be run against a future package candidate, but they are not part of the minimal EC-7 metadata package unless QA requests them.

### Deferred Micro-Reports

Deferred micro-slice reports from EC-7D/EC-7E/EC-7F remain archive/traceability candidates. The default package includes summary/closure reports only; full micro-report inclusion requires QA traceability approval.

## Future Clean Package Procedure

1. Create a clean worktree from the target base.
2. Apply Bundle A full-file candidates first.
3. Verify missing internal imports are zero, fake-Frappe service import passes, guardrail passes, and direct assistant inventory remains `0 / 1 / 27`.
4. Apply Bundle B full-file candidates.
5. Apply Bundle B hunk-aware candidates with explicit hunk review; never whole-file stage `service.py` without separate approval.
6. Exclude Bundle C JSON unless QA explicitly approves generated evidence inclusion.
7. Run staged/cached-index verification only after staging is explicitly approved.
8. Do not commit/push until Counterpart/QA approve the staged package candidate.

## Required Future Verification

- Guardrail.
- Fake-Frappe service import.
- Static service import integrity scan.
- Direct assistant inventory `0 / 1 / 27`.
- Raw assistant append scan only `authorized_emission.py:271` and `authorized_emission.py:327`.
- EC-7 metadata/probe/soft-gate tests.
- Authorized-emission regression checks.
- Scoped diff check.
- Excluded stream scans.
- Staged/cached-index verification after staging approval.

## Non-Goals

- `no_staging`
- `no_commit`
- `no_push`
- `no_cleanup`
- `no_strict_enforcement`
- `no_runtime_behavior_change`
- `no_ec_7h_live_trace_work`
- `no_deployment`
- `no_ux_filter_mi_family_expansion`

## Final Recommendation

`ec_7p_c_clean_package_dry_run_manifest_ready_for_counterpart_review`
