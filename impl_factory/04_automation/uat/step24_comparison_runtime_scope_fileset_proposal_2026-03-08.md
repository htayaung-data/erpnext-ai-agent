# Comparison Runtime Scope / File-Set Proposal

Date: 2026-03-08  
Updated: 2026-03-17  
Owner: AI Runtime Engineering  
Scope: Checkpoint-2 proposal before any comparison runtime implementation edits  
Status: pending approval

## Purpose
This document provides the exact file scope for comparison first-slice implementation under strict change control.

No runtime code edits are allowed until this proposal is approved.

## Current Worktree State (Already Dirty Files)
Current dirty files are documentation-only from Step 1 planning plus unrelated governance work:

1. [step22_comparison_class_strict_implementation_contract_2026-03-07.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step22_comparison_class_strict_implementation_contract_2026-03-07.md)
2. [step23_first_approved_expansion_candidate_comparison.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_first_approved_expansion_candidate_comparison.md)
3. [step23_comparison_asset_preparation_checklist.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_asset_preparation_checklist.md)
4. [step23_comparison_ontology_planning.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_ontology_planning.md)
5. [step23_comparison_capability_metadata_planning.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_capability_metadata_planning.md)
6. [step23_comparison_variation_matrix.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_variation_matrix.md)
7. [step23_comparison_replay_asset_design.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_replay_asset_design.md)
8. [step23_comparison_manual_golden_pack.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_manual_golden_pack.md)
9. [step23_comparison_approval_review_2026-03-07.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_approval_review_2026-03-07.md)
10. [step24_comparison_runtime_scope_fileset_proposal_2026-03-08.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step24_comparison_runtime_scope_fileset_proposal_2026-03-08.md)
11. [step25_comparison_checkpoint3_edit_batch_plan_2026-03-08.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step25_comparison_checkpoint3_edit_batch_plan_2026-03-08.md)

Unrelated dirty files outside this comparison slice:

1. [README.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/README.md)
2. [nemoclaw_evaluation_2026-03-17.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/nemoclaw_evaluation_2026-03-17.md)

Mixed-worktree rule:

1. do not start runtime edits while these planning docs are still uncommitted/unapproved
2. lock Step 1 docs first, then start runtime slice
3. do not touch unrelated governance files during comparison implementation

## Proposed In-Scope Files (Runtime/Data For Comparison First Slice)

### Contract / Ontology / Metadata Surfaces

1. [spec_contract_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/spec_contract_v1.json)
2. [clarification_contract_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/clarification_contract_v1.json)
3. [ontology_base_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/ontology_base_v1.json) (only if first-slice comparison aliases are missing)
4. [capability_registry_overrides_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/capability_registry_overrides_v1.json)
5. [contract_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contract_registry.py) (only if new contract keys are required)

### Runtime Surfaces

1. [spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/spec_pipeline.py)
2. [semantic_resolver.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/semantic_resolver.py)
3. [constraint_engine.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/constraint_engine.py) (only if entity-vs-entity constraint support is needed)
4. [read_engine.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/read_engine.py) (only for safe unsupported/clarification envelopes if needed)
5. [shaping_policy.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/shaping_policy.py) (only if comparison default columns require governed shaping support)

## Proposed In-Scope Files (Tests / Replay / Evidence)

1. [test_v7_spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_spec_pipeline.py)
2. [test_v7_read_engine_clarification.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_read_engine_clarification.py) (only if clarification behavior changes)
3. [test_v7_read_execution_runner.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_read_execution_runner.py) (only if result mode shaping path changes)
4. [core_read.jsonl](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/replay_v7_expanded/core_read.jsonl) (for comparison cases)
5. [manifest.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/replay_v7_expanded/manifest.json) (only if suite-level replay structure must be updated)
6. new comparison evidence/closure docs under `/impl_factory/04_automation/uat/`

## Explicit Excluded Files
The following are out of scope for comparison first-slice implementation:

1. UI/frontend files (including chat page JS/CSS)
2. write-path modules and write-safety logic
3. threshold and contribution policy modules unless regression-only evidence requires it
4. unrelated UAT historical closure docs
5. operational runbook documents not tied to this class slice

## Guardrail Notes

1. first slice now includes same-period comparison, monthly period-vs-period, and bounded MoM only
2. weekly/quarterly/YoY and multi-point time-series asks must remain outside this class boundary
3. full trend lines remain owned by the existing `trend_time_series` class
4. no prompt-to-report routing maps
5. no case-ID logic in runtime
6. no keyword hacks for business routing

## Approval Request
If approved:

1. lock/commit Step 1 planning docs
2. start Checkpoint-3 preparation (exact edit batch plan by file)
3. stop again before first runtime edit
