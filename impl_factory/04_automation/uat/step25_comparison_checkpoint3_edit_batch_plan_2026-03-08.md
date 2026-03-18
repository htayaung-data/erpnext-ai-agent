# Comparison Checkpoint 3 Edit-Batch Plan

Date: 2026-03-08  
Updated: 2026-03-17  
Owner: AI Runtime Engineering  
Scope: exact pre-edit plan for first runtime implementation slice of `comparison`  
Status: planning only (no runtime edits yet)

## Purpose
This is the strict Checkpoint-3 plan required before first code edit.

It defines:

1. exact edit batches
2. exact files per batch
3. why each file is needed
4. excluded files
5. required validation sequence

## Current Worktree (Pre-Edit)
Already-dirty files (docs only):

1. `step22_comparison_class_strict_implementation_contract_2026-03-07.md`
2. `step23_*` comparison planning docs (8 files)
3. `step24_comparison_runtime_scope_fileset_proposal_2026-03-08.md`

No runtime files are currently modified.

## Approved First-Slice Boundary (Implementation)

### In Scope

1. same-period entity-vs-entity comparison
2. monthly period-vs-period comparison
3. bounded MoM comparison
4. deterministic clarification/unsupported handling for missing inputs and out-of-scope period structures

### Out Of Scope

1. weekly comparisons
2. quarterly comparisons
3. YoY and non-month period comparisons
4. multi-point time-series output
5. advisory interpretation

## Exact Edit Batches

### Batch 1: Contract/Ontology Surface
Goal:

1. encode comparison class semantics in governed contract/ontology surfaces

Files:

1. [spec_contract_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/spec_contract_v1.json)
2. [clarification_contract_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/clarification_contract_v1.json)
3. [ontology_base_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/ontology_base_v1.json)
4. [ontology_normalization.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/ontology_normalization.py)
5. [contract_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contract_registry.py)

Planned changes:

1. add `comparison` to allowed task classes
2. add `comparison` task-class rule with allowed dimensions and allowed time-comparison structures for first slice
3. add clarification question keys for comparison missing inputs
4. add ontology-governed comparison scope aliases for same-period, monthly period-vs-period, and MoM detection
5. add helper in ontology normalization to infer allowed comparison time structures
6. mirror default fallback contract in `contract_registry.py`

### Batch 2: Spec Pipeline Normalization
Goal:

1. classify first-slice comparison asks deterministically
2. classify monthly period-vs-period and bounded MoM asks without collapsing them into generic trend behavior
3. gate unsupported weekly/quarterly/YoY/multi-point time-series asks before resolver execution

Files:

1. [spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/spec_pipeline.py)

Planned changes:

1. add comparison signal extraction using ontology-derived terms
2. set `task_class = comparison` for same-period, monthly period-vs-period, and bounded MoM asks (without hijacking contribution/threshold or trend time-series)
3. set bounded missing-filter markers:
   - comparison metric missing
   - comparison dimension missing
   - comparison month anchor missing
4. set unsupported marker for weekly/quarterly/YoY/non-month period asks in first slice
5. preserve existing threshold, contribution, and `trend_time_series` behavior order/invariants

### Batch 3: Runtime Precheck Envelope
Goal:

1. produce deterministic safe unsupported text/error-envelope for weekly/quarterly/YoY/non-month period asks
2. produce deterministic clarification for missing comparison inputs or missing monthly anchor

Files:

1. [read_engine.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/read_engine.py)

Planned changes:

1. add `_comparison_unsupported_text` and `_comparison_error_payload`
2. add `_comparison_precheck` similar in pattern to threshold/contribution prechecks
3. wire precheck into main read flow before resolver execution
4. keep multi-point trend output on the existing `trend_time_series` path
5. do not modify write-path, transform core, or UI paths

### Batch 4: Unit/Module Tests
Goal:

1. lock invariants and prevent regression reintroduction

Files:

1. [test_v7_spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_spec_pipeline.py)
2. [test_v7_read_engine_clarification.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_read_engine_clarification.py)
3. [test_v7_contract_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_contract_registry.py)
4. [test_v7_ontology_normalization.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_ontology_normalization.py)

Planned tests:

1. plain same-period comparison ask remains comparison class, not contribution hijack
2. explicit monthly period-vs-period ask is classified as comparison
3. explicit MoM ask is classified as comparison with bounded monthly semantics
4. weekly/quarterly/YoY asks are marked unsupported in first slice
5. missing comparison inputs or missing monthly anchor trigger clarification path
6. contract registry exposes new comparison class and question keys
7. ontology comparison scope inference works as expected
8. multi-point trend asks remain on the existing `trend_time_series` path

### Batch 5: Replay Asset Preparation (Comparison Suite)
Goal:

1. provide class-specific replay coverage independent of core packs

Files:

1. [comparison_class.jsonl](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/replay_v7_expanded/comparison_class.jsonl) (new)
2. [manifest.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/replay_v7_expanded/manifest.json)

Planned changes:

1. add bounded first-slice comparison cases (same-period, monthly period comparison, MoM, follow-up, clarification, unsupported)
2. register new suite in manifest packs
3. update total case count accordingly

## Explicitly Excluded Files

1. frontend/UI files (`ai_chat.js`, CSS, page templates)
2. write safety modules and write confirmation paths
3. threshold/contribution policy modules unless a test proves direct breakage
4. unrelated UAT historical closure docs

## Validation Plan (Post-Implementation)

### Unit/Module

1. `test_v7_spec_pipeline`
2. `test_v7_read_engine_clarification`
3. `test_v7_contract_registry`
4. `test_v7_ontology_normalization`

### Replay (Targeted First)

1. `--suite comparison_class` full
2. selected probes from existing `core_read` comparison family (`CMP-*`)
3. selected boundary probes from existing `trend_time_series` coverage

### Impacted Suites

1. `core_read`
2. `multiturn_context` (if follow-up behavior touched)
3. `transform_followup` (if transform/active-result reuse touched)

### Manual/Browser

1. execute `step23_comparison_manual_golden_pack.md`

## Stop Rule
No runtime edit starts until this plan is approved.

Any required file outside this plan triggers stop-and-ask before editing.
