# Comparison Contract Remediation Plan

Date: 2026-03-17  
Owner: AI Runtime Engineering  
Scope: corrective plan after comparison implementation drift review  
Status: planning only, no runtime edits in this step

## Purpose

This note records the corrective path after the first `comparison` implementation drifted outside the approved contract boundary.

It classifies current work into:

1. keep
2. rewrite
3. revert

No new runtime behavior may be added until this remediation plan is executed.

## Audit Outcome

The current `comparison` implementation contains useful contract additions, but runtime behavior drifted in three ways:

1. message-shape parsing was added directly in runtime modules
2. report-specific execution policy was hardcoded in engine code
3. replay rigor was weakened through case-specific shape-only rules

This is not acceptable as enterprise closure-grade implementation.

## Keep (Aligned With Contract)

These changes are directionally correct and should remain, with only normal validation:

1. `comparison` class contract surface in [spec_contract_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/spec_contract_v1.json)
2. comparison clarification keys in [clarification_contract_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/clarification_contract_v1.json)
3. comparison ontology vocabulary in [ontology_base_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/ontology_base_v1.json)
4. comparison contract accessors in [contract_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contract_registry.py)
5. capability metadata additions in [capability_registry_overrides_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/capability_registry_overrides_v1.json), subject to metadata-only discipline
6. comparison replay asset skeleton in [comparison_class.jsonl](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/replay_v7_expanded/comparison_class.jsonl) and manifest registration in [manifest.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/replay_v7_expanded/manifest.json)

## Rewrite (Must Stay, But Must Be Redesigned)

These areas should not be kept as currently implemented. The capability is needed, but the implementation must be rewritten.

### 1. Ontology Normalization Helper Logic

File:

1. [ontology_normalization.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/ontology_normalization.py)

Problem:

1. comparison inference mixes ontology-backed aliases with extra runtime regex heuristics
2. month-pair detection logic is embedded in code instead of being a thin structural interpreter over contract-backed signals

Rewrite rule:

1. keep comparison public helpers if useful
2. remove speculative regex enrichment that is not strictly needed
3. allow only:
   - ontology alias lookup
   - bounded structural extraction for month references
4. no direct message-intent forcing beyond approved contract outputs

### 2. Spec Pipeline Comparison Normalization

File:

1. [spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/spec_pipeline.py)

Problem:

1. comparison routing currently depends on direct regex parsing of user text
2. stop-cue parsing, operand slicing, and relative time inference are over-embedded in runtime code
3. this is the main contract breach

Rewrite rule:

1. comparison normalization must consume:
   - ontology-backed comparison signal
   - existing canonical dimension and metric normalization
   - explicit planner/spec fields
2. any structural extraction must be minimal and domain-agnostic
3. remove direct phrase parsing blocks that act like a local keyword parser

### 3. Read Engine Comparison Policy

File:

1. [read_engine.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/read_engine.py)

Problem:

1. unsupported comparison text is embedded in code
2. execution defaults branch directly on report names
3. filter-field mapping is hardcoded in engine logic

Rewrite rule:

1. precheck pattern may remain, but policy text should come from contract/config
2. report execution defaults must move to metadata or an adapter layer
3. engine code should apply metadata, not own report-name behavior

## Revert (Current Form Should Be Removed)

These specific changes should be removed in their current form before we claim contract alignment.

### 1. Shape-Only Downgrade For New Comparison Cases

File:

1. [semantic_assertions.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/semantic_assertions.py)

Revert rule:

1. remove `CMPC-*` from `SHAPE_ONLY_CASES`
2. replace with stronger semantic assertions once runtime behavior is rebuilt

### 2. Case-Specific Comparison Pass Rules

File:

1. [run_phase6_canary_uat.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/run_phase6_canary_uat.py)

Revert rule:

1. remove tactical `CMPC-*` pass branches that validate only local shape heuristics
2. rebuild suite checks around approved comparison semantics, not case-local expectations

### 3. Runtime Lexical Parsing Blocks In Current Comparison Implementation

File:

1. [spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/spec_pipeline.py)

Revert rule:

1. remove direct stop-cue regex and operand parsing in current form
2. replace with minimal contract-aligned extraction only

## Strict Remediation Order

The correction sequence must be:

1. freeze current comparison implementation state
2. remove replay-rigor downgrade
3. rewrite ontology-normalization comparison inference to stay thin and contract-backed
4. rewrite `spec_pipeline.py` comparison normalization
5. move comparison execution defaults from `read_engine.py` into metadata-driven behavior
6. restore comparison replay assertions with stronger semantics
7. rerun targeted unit tests
8. rerun `comparison_class`
9. rerun impacted suites only after targeted comparison is stable

## Guardrails For The Rewrite

1. no case-ID logic in runtime
2. no direct prompt-to-report mapping in runtime
3. no new hardcoded phrase lists in `spec_pipeline.py` or `read_engine.py`
4. ontology vocabulary may exist only in contract data, not duplicated into business routing logic
5. metadata may describe report capability, but engine code must not branch on business phrases

## Definition Of Contract Recovery

The `comparison` implementation is back inside contract boundary only when all are true:

1. runtime routing is contract/ontology/metadata-driven
2. replay suite is not relying on tactical shape-only downgrade
3. report execution defaults are metadata-driven or adapter-driven
4. unsupported and clarification paths are policy-backed, not scattered text conditionals
5. targeted replay and impacted reruns are green

## Immediate Next Step

Before any new `comparison` code is added:

1. approve this remediation plan
2. execute the rewrite against only the approved runtime files
3. stop again before replay changes are finalized
