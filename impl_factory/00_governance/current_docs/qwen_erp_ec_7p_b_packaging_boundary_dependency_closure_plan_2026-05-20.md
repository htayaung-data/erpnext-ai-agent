# EC-7P-B Packaging Boundary And Dependency Closure Plan

Decision: ec_7p_b_packaging_boundary_dependency_closure_plan_ready_for_counterpart_review

Date: 2026-05-20
Generated: 2026-05-19T18:37:48+00:00
Branch: feature/ec-7b0-runtime-import-integrity
Head: 2641458
Compact dirty count (`git status --short`): `132`
Expanded dirty count (`git status --porcelain=v1 -uall`): `135`
Staged files count: `0`
Runtime effect: `none`
Packaging action performed: `none`

## Scope

EC-7P-B is a packaging boundary and dependency-closure plan only. It does not stage, commit, clean, enforce, change runtime behavior, run live UAT, deploy, or start strict enforcement.

EC-7 remains backend-ready for metadata/provenance review, but not production launch and not strict enforcement.

## Proposed Bundle Boundary

| Bundle | Purpose | Packaging recommendation |
|---|---|---|
| Bundle A: EC-7B0 runtime import/dependency integrity | Restore runtime modules required for clean service import and accepted EC-7 runtime dependency closure. | Package first or as a clearly separated dependency bundle. Use whole-file only for new restored modules; verify fake-Frappe service import from clean package. |
| Bundle B: EC-7 metadata/provenance/soft-gate implementation | Metadata contract, deterministic/control wiring, AI/helper provenance wiring, runtime probes, soft-gate dry-run source/tests, and governance reports. | Package after Bundle A dependency closure is proven. Use hunk-aware staging for broad existing runtime files. |
| Bundle C: generated evidence | EC-7 generated JSON/selected generated reports only if Counterpart/QA explicitly approve versioning them. | Keep optional. Do not package broad generated directories. Archive non-source-of-truth artifacts outside release source if needed. |

## Bundle A Candidate: Runtime Import / Dependency Integrity

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/analytical_scope_policy.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/assistant_formatting.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/boundary_contract_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compound_request_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/grounded_context.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/message_history.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/context/session_context.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/conversation_control_decisions.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/conversation_control_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/conversation_snapshot.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_composite_runtime_execution.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_runtime_execution.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/compiled_query_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/entity_drilldown_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/repair_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metric_union_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recent_focus_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recovery_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/requery_message_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/restore_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/rollout.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_message_compilation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/scope_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/turn_journal.py`

Bundle A dependency-closure rule: every restored module must be justified by service import, active runtime import, or accepted test/runtime dependency. No broad old-branch copy is allowed.

## Bundle B Candidate: EC-7 Metadata Source

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_metadata_contract.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/light_semantic_metadata.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_backed_helper_metadata.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/strict_readiness_soft_gate.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/artifact_narrative.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_system.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/composite_reads.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/reasoning_execution.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_interpreter.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_reasoning_activation.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_repair_intent.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/runtime_gate_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/local_followup_support.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_coverage.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_observability.py`

## Hunk-Aware Files

| File | Why hunk-aware |
|---|---|
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | broad orchestrator; include only EC-7 metadata/control helper hunks after hunk audit |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py` | contains compiled-read helper/runtime provenance plus broader fresh-query behavior; hunk audit required |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_intent_gate.py` | frontdoor semantic metadata provenance mixed with pre-existing/frontdoor behavior; hunk audit required |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py` | NBU deterministic metadata mixed with NBU business behavior; hunk audit required |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_runtime.py` | NBU shadow observer metadata mixed with runtime behavior; hunk audit required |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py` | NBU safe/control metadata mixed with activation behavior; hunk audit required |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py` | visible-context deterministic/control metadata mixed with follow-up logic; hunk audit required |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_trace_inspection.py` | trace/control metadata mixed with trace inspection logic; hunk audit required |

Hunk-aware rule: do not whole-file stage these files in a future package attempt unless Counterpart/QA explicitly approve. A future EC-7P-C package build should use hunk-level review and cached-index tests.

## Bundle B Candidate: Tests

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

Test packaging rule: include focused EC-7 metadata/probe/soft-gate tests and only the existing authorized-emission tests needed to prove no regression. Broader suites should be verification commands, not automatically bundled if unrelated.

## Bundle B Candidate: Governance Reports

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

Governance report rule: include accepted EC-7 summary/closure reports and this plan. Avoid duplicating every micro-slice report in a minimal PR unless QA requests full traceability.

## Bundle C Candidate: Generated Evidence

- `impl_factory/00_governance/current_docs/qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.json`

Generated evidence rule: version the EC-7G-B JSON only if QA wants machine-readable soft-gate evidence in repo. Otherwise archive outside source and keep Markdown governance as source-of-truth.

## Explicit Exclusions

- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_cli_report.json`
- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_cli_report.md`
- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_resilience_runner_contract.json`
- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_resilience_runner_contract.md`
- ERP UI streams, seed/data, dummy data, temp/probe/cache files, PrimeAxis owner docs, UX, Filter, MI, family expansion, deployment files, and strict-enforcement runtime changes remain excluded.

## Dependency Closure Plan

1. Build a clean worktree from current target base before any staging attempt.
2. Apply Bundle A first and verify static missing internal imports are zero, fake-Frappe service import passes, guardrail passes, and direct assistant inventory remains `0 / 1 / 27`.
3. Apply Bundle B with hunk-aware staging for the broad runtime files listed above.
4. Run EC-7 metadata/probe/soft-gate tests against the staged/cached package, not only the dirty worktree.
5. Run raw assistant append scan against the staged package and require only `authorized_emission.py:271` and `authorized_emission.py:327`.
6. Decide Bundle C generated evidence inclusion after Counterpart/QA review.
7. Do not commit or push until Counterpart/QA accept the staged package candidate.

## Packaging Readiness Decision

Current status: `not_packageable_yet_due_to_dependency_closure_and_hunk_boundary_needing_review`.

Recommended next slice, if accepted: EC-7P-C clean package dry-run manifest / dependency ledger. Still no staging unless explicitly approved.

## Non-Goals

- `no_staging`
- `no_commit`
- `no_cleanup`
- `no_strict_enforcement`
- `no_runtime_behavior_change`
- `no_live_uat_or_probe_expansion`
- `no_deployment`
- `no_ux_filter_mi_family_expansion`

## Final Recommendation

`ec_7p_b_packaging_boundary_dependency_closure_plan_ready_for_counterpart_review`
