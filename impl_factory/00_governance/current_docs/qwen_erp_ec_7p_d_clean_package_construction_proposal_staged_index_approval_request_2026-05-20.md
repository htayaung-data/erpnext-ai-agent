# EC-7P-D Clean Package Construction Proposal / Staged-Index Approval Request

Decision: ec_7p_d_clean_package_construction_proposal_ready_for_counterpart_qa_review

Date: 2026-05-20
Generated: 2026-05-20T03:25:17+00:00
Branch: feature/ec-7b0-runtime-import-integrity
Head: 2641458
Runtime effect: `none`
Staging performed: `false`
Commit/push performed: `false`
Current expanded dirty count after this report: `138`
Staged files count: `0`

## Scope

EC-7P-D is proposal/report only. It is a request for Counterpart/QA approval to attempt future staged-index package construction. It is not staging approval, not commit approval, and not push approval.

No staging, commit, push, cleanup, EC-7H live trace work, strict enforcement, runtime behavior change, deployment, UX, Filter, MI, or family expansion was performed.

## Future Staging Plan: Bundle A Full-File Files

Stage these 44 files whole-file only after approval, because EC-7P-B-A classifies them as restored EC-7B0 runtime import/dependency integrity files.

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

## Future Staging Plan: Bundle B Full-File Files

Stage these 29 files whole-file only after approval, because they are new EC-7 metadata/probe/soft-gate files, focused tests, or accepted summary governance reports. This count increased from the EC-7P-C dry-run manifest because the EC-7P-D staged-index approval request report itself is now included as a future governance report.

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
- `impl_factory/00_governance/current_docs/qwen_erp_ec_7p_d_clean_package_construction_proposal_staged_index_approval_request_2026-05-20.md`

## Future Hunk-Aware Plan: Bundle B Runtime/Source Files

These 25 files require hunk-level staging. Whole-file staging is not approved by this proposal.

| File | Future staging rule |
|---|---|
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/artifact_narrative.py` | stage only helper provenance metadata envelope hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_system.py` | stage only helper provenance metadata envelope hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support.py` | stage only deterministic/control metadata envelope hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/composite_reads.py` | stage only governed-tool runtime metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py` | stage only entity follow-up deterministic/error metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py` | stage only light-semantic and compiled-read provenance hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_intent_gate.py` | stage only frontdoor semantic metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py` | stage only artifact-boundary metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py` | stage only clarification/control metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py` | stage only legacy deterministic/policy/error metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py` | stage only reasoning metadata surface hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/runtime_gate_lane.py` | stage only runtime-gate policy metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/local_followup_support.py` | stage only local follow-up deterministic metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_coverage.py` | stage only metadata coverage/soft-readiness helper hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/model_role_observability.py` | stage only model-role observability hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py` | stage only NBU governed-requery metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_runtime.py` | stage only NBU shadow observer metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py` | stage only NBU safe/control metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/reasoning_execution.py` | stage only heavy-reasoning provenance hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_interpreter.py` | stage only light-semantic metadata/status guard hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_reasoning_activation.py` | stage only semantic reasoning activation metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_repair_intent.py` | stage only semantic repair intent metadata hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | stage only EC-7B0 import integrity and service policy/control metadata hunks; never whole-file |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py` | stage only visible-context metadata consistency hunks |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_trace_inspection.py` | stage only trace/control metadata hunks |

## Must Remain Unstaged Unless Separately Approved

- 19 deferred EC-7 micro-slice governance reports unless QA requests full traceability.
- 4 excluded S7 generated files under impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_*.
- Bundle C generated JSON: impl_factory/00_governance/current_docs/qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.json unless QA explicitly approves.
- ERP UI, seed/data, dummy data, temp/probe/cache, .codex_tmp, PrimeAxis docs, unrelated generated files.
- Any broad non-EC-7 runtime behavior hunks in hunk-aware files.

Future exclusion check must prove no ERP UI, seed/data, dummy data, temp/probe/cache, `.codex_tmp`, PrimeAxis docs, unrelated generated files, or excluded broad streams enter the staged package.

## Proposed Staged-Index Verification Commands After Approval

Run these only after Counterpart/QA explicitly approve a staging attempt:

- `git diff --cached --name-only | wc -l`
- `git diff --cached --name-only | grep -E 'erp_workspace_ui|02_seed_data|dummy_data|tmp/|\.codex_tmp|primeaxis|generated/qwen_s7_browser_batch' || true`
- `git grep --cached -n 'append_message(session_doc, "assistant"' -- impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat`
- `python3 scripts/check_qwen_enterprise_guardrails.py`
- `git diff --cached --check`
- `git diff --check -- impl_factory/05_custom_logic/custom_app/ai_assistant_ui impl_factory/00_governance/current_docs`
- `PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q ai_assistant_ui.tests.test_runtime_metadata_contract ai_assistant_ui.tests.test_light_semantic_runtime_metadata_contracts ai_assistant_ui.tests.test_light_semantic_runtime_probes ai_assistant_ui.tests.test_heavy_shadow_runtime_metadata_contracts ai_assistant_ui.tests.test_heavy_reasoning_nbu_shadow_runtime_probes ai_assistant_ui.tests.test_model_backed_helper_metadata_wiring ai_assistant_ui.tests.test_governed_tool_runtime_metadata_wiring ai_assistant_ui.tests.test_service_validator_provenance_probes ai_assistant_ui.tests.test_helper_tool_runtime_probes ai_assistant_ui.tests.test_deterministic_control_runtime_metadata_probes ai_assistant_ui.tests.test_strict_readiness_soft_gate`
- `PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q ai_assistant_ui.tests.test_authorized_emission_contracts`
- `python3 -m compileall -q impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests`
- `fake-Frappe import probe for ai_assistant_ui.qwen_chat.service from the staged/clean package worktree`
- `static service import integrity scan from the staged/clean package worktree`

## Approval Request

Requested approval is limited to a future staged-index package construction attempt using the Bundle A, Bundle B full-file, and Bundle B hunk-aware boundaries above. It does not approve commit, push, strict enforcement, runtime behavior changes, deployment, or EC-7H live trace work.

## Non-Goals

- `no_staging_in_ec_7p_d`
- `no_commit`
- `no_push`
- `no_cleanup`
- `no_strict_enforcement`
- `no_runtime_behavior_change`
- `no_ec_7h_live_trace_work`
- `no_deployment`
- `no_ux_filter_mi_family_expansion`

## Final Recommendation

`ec_7p_d_clean_package_construction_proposal_ready_for_counterpart_qa_review`
