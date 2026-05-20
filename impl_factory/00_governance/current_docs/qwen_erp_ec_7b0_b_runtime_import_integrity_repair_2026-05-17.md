# EC-7B0-B Runtime Import Integrity Repair Closure Report

Date: 2026-05-17

## Executive Decision

Status: ready_for_counterpart_and_qa_review

EC-7B0-B repaired the clean-main runtime import boundary enough for `ai_assistant_ui.qwen_chat.service` to import under a fake-Frappe probe. This is a runtime import integrity repair only. It does not implement EC-7 model-role metadata wiring, strict model-role enforcement, UX, Filter, MI, family expansion, service refactor, cleanup, staging, commit, push, or deployment.

## Branch / Head

| Field | Value |
|---|---|
| Worktree | `/tmp/erpai_ec7b0_import_integrity` |
| Branch | `feature/ec-7b0-runtime-import-integrity` |
| Base | `origin/main` |
| HEAD | `2641458` |
| Staged files | `0` |

## Changed Files

Modified files:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_interpreter.py`

Restored untracked dependency files:

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

## Active Runtime Dependencies Restored

The active dependency set was restored because `service.py` imports or reaches these modules through active runtime paths. The repair avoided wholesale restoration of smoke/evaluation/probe modules.

Active dependency categories restored:

- Session/message/grounding helpers: `context/session_context.py`, `context/message_history.py`, `context/grounded_context.py`, `conversation_snapshot.py`, `turn_journal.py`.
- Runtime control and follow-up helpers: `conversation_control_support.py`, `conversation_control_decisions.py`, `compound_request_support.py`, `continuation_support.py`, `recent_focus_support.py`, `restore_support.py`, `runtime_message_compilation.py`, `scope_support.py`, `recovery_support.py`, `requery_message_support.py`, `runtime_support.py`, `rollout.py`.
- Active lanes: `lanes/compiled_query_lane.py`, `lanes/entity_drilldown_lane.py`, `lanes/repair_lane.py`.
- Boundary/formatting helpers: `boundary_contract_support.py`, `assistant_formatting.py`.
- KPI/composite/entity-reference dependencies: `governed_composite_runtime_execution.py`, `governed_kpi_runtime_execution.py`, `governed_kpi_execution_state.py`, `governed_kpi_execution_registry.py`, `governed_kpi_support.py`, `business_definition_state.py`, `business_rule_registry.py`, `business_threshold_state.py`, `customer_kpi_runtime_support.py`, `customer_lifecycle_support.py`, `entity_period_aggregation_support.py`, `entity_reference_resolution.py`, `master_data_frontdoor_support.py`, `master_data_lookup_support.py`, `metric_union_support.py`, `ranking_limit_parser.py`, `collections_support.py`, `analytical_scope_policy.py`, `composite_artifact_state.py`, `defaults_repository.py`, `framework/`.

## Lazy-Deferred Smoke / Evaluation / Probe Imports

`service.py` now lazy-defers optional smoke/evaluation/probe helpers using `_lazy_symbol(...)`. These modules are no longer top-level import blockers for runtime service import.

Lazy-deferred categories:

- `audit_support.py`
- `snapshot_defaults.py`
- `smoke_fixtures.py`
- `family_evaluation_support.py`
- `phase55_hardening_support.py`
- `phase6_hardening_support.py`
- `phase7_hardening_support.py`
- `phase8_hardening_support.py`
- `smoke_session_support.py`
- `evaluation/*`
- `probes/service_diagnostics.py`

Note: `phase8_hardening_support.py` still imports `smoke_fixtures.py`, but it is no longer top-level imported by `service.py`; it is deferred behind `_lazy_symbol(...)` as optional smoke support.

No source change is required for `phase8_hardening_support.py` in EC-7B0-B. Its raw assistant append is not part of the active runtime emission inventory because the module is optional smoke/recovery support and is lazy-deferred from `service.py`.

## Explicit Approval Rationale

`assistant_formatting.py`: Approved EC-7B0 dependency exception. `service.py` actively imports formatting helpers including `_assistant_text_payload_helper`, table normalization, and million-format transforms. Runtime importability cannot be honestly restored without this module or an equivalent narrow reconstruction.

`context/grounded_context.py`: Approved EC-7B0 dependency exception. `service.py` actively imports grounded context helpers used by continuation, visible context, reasoning, and report-result authority paths. It is required for runtime import integrity before metadata coverage can be evaluated.

`scope_support.py`: Approved EC-7B0 dependency exception. `service.py` actively imports scope and boundary support helpers used by runtime gate, follow-up suppression, and out-of-scope response paths. It is required for active service importability.

`governed_kpi_support.py`: Reclassified from optional smoke/probe support to required transitive runtime dependency. `clarification_resolution.py` imports `maybe_build_governed_kpi_frontdoor_response` directly, so excluding it prevents `service.py` from importing even when smoke/evaluation modules are deferred.

## Verification Results

| Check | Result |
|---|---|
| `service.py` missing internal import count | `0` |
| Fake-Frappe service import probe | PASS |
| Guardrail | PASS |
| Runtime emission inventory | Clean: active runtime direct assistant append count is `0`; active assistant emission remains centralized through authorized helper paths |
| Raw working-tree append scan | Includes `authorized_emission.py:271`, `authorized_emission.py:327`, and `phase8_hardening_support.py:68` |
| `phase8_hardening_support.py:68` classification | Optional smoke/recovery support, lazy-deferred from `service.py`, non-runtime for EC-7B0-B |
| Source scan | `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths_length=27` |
| Scoped AI diff check | PASS |
| Final authority/emission tests | `47 passed` |
| Visible-context suite | `78 passed` |
| NBU suite | `153 passed` |
| Manual UAT suite | `170 passed` |
| Narrow semantic runtime-gate authority test | `1 passed` |
| Python compile | PASS, `181` files |

## Exclusions / Non-Goals

No ERP UI, seed/data, temp/probe/cache cleanup, UX, Filter, MI, family expansion, service refactor, model-role metadata wiring, model-role strict enforcement, staging, commit, push, or deployment was performed.

The four generated scratch files remain untracked and excluded:

- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_cli_report.json`
- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_cli_report.md`
- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_resilience_runner_contract.json`
- `impl_factory/00_governance/current_docs/generated/qwen_s7_browser_batch_resilience_runner_contract.md`

## Final Recommendation

`ec_7b0_b_runtime_import_integrity_repair_ready_for_counterpart_and_qa_review`

Next recommended slice after acceptance: EC-7B Runtime Metadata Coverage Inventory, dry-run/metadata mapping only. Do not start model-role strict enforcement until coverage and runtime metadata provenance are accepted.
