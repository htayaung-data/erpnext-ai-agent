# Contribution Share Implementation Plan

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: controlled implementation plan for `contribution_share`  
Status: implementation planning approved for the first bounded slice

## Purpose
This document turns the approved expansion candidate into a concrete build sequence.

The goal is to implement in an enterprise-safe way:

1. ontology and metadata first
2. runtime changes second
3. targeted validation third
4. broader regression evidence after that

This is not release approval.  
This is the controlled implementation plan.

## Class Name
- `contribution_share`

## Approved First Slice
The first implementation slice is limited to deterministic contribution-share behavior for:

1. customers by revenue
2. suppliers by purchase amount
3. items by revenue

Approved first-slice report families:

1. `Customer Ledger Summary`
2. `Supplier Ledger Summary`
3. `Item-wise Sales Register`

## Explicit Non-Goals For This Implementation
Do not implement in this first slice:

1. territory/group-share variants
2. cumulative / Pareto share
3. concentration-risk analysis
4. advisory or recommendation behavior
5. time-comparison share behavior
6. write/action flows

## Contract Boundary Rules
Implementation must remain inside the established project boundary.

Must not do:

1. prompt-to-report routing maps
2. case-ID hacks
3. runtime business keyword routing
4. hidden fallback logic that cannot be explained by ontology, metadata, or persisted state

Must do:

1. use ontology for share/contribution language
2. use capability metadata for contribution-capable metrics and dimensions
3. keep runtime generic
4. preserve current follow-up and projection contracts

## Implementation Strategy

### Step 1: Governed Ontology Additions
Add only the reviewed first-slice ontology semantics:

1. contribution/share aliases
2. percent-of-total aliases
3. first-slice grain aliases already in scope

Primary likely files:

1. [ontology_base_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/ontology_base_v1.json)
2. [ontology_normalization.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/ontology_normalization.py)

### Step 2: Capability Metadata Additions
Declare contribution-ready behavior in governed metadata before runtime logic depends on it.

Required metadata additions:

1. `contribution_metrics`
2. safe first-turn output columns
3. aggregate-row policy where relevant

Primary likely files:

1. [capability_registry_overrides_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/capability_registry_overrides_v1.json)
2. [capability_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/capability_registry.py)

### Step 3: Class Contract Representation
Introduce the class in a controlled, explicit way.

Required:

1. class identity in planning/runtime contract layer
2. approved output modes
3. approved follow-up semantics
4. clarification rules for missing metric or grain

Primary likely files:

1. [spec_contract_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/spec_contract_v1.json)
2. [contract_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contract_registry.py)
3. [spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/spec_pipeline.py)
4. [spec_schema.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/spec_schema.py)

### Step 4: Resolver Support
Add generic resolver support for contribution-share reads using governed metadata only.

Runtime should:

1. match canonical metric + grain to contribution-capable reports
2. reject reports that do not support contribution-safe execution for that metric
3. prefer customer revenue, supplier purchase amount, and item revenue paths only in the approved first slice

Primary likely files:

1. [constraint_engine.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/constraint_engine.py)
2. [semantic_resolver.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/semantic_resolver.py)

### Step 5: Deterministic Contribution Calculation
Implement deterministic contribution-share calculation without breaking current read behavior.

Rules:

1. compute contribution share from the returned row set after aggregate-row exclusion
2. preserve entity grain
3. preserve base metric
4. write the derived share into payload metadata and visible table shape
5. preserve `_source_table` for follow-up projection/top-n behavior

Primary likely files:

1. a new bounded helper module:
   - [contribution_share_policy.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contribution_share_policy.py)
2. [read_engine.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/read_engine.py)
3. [read_execution_runner.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/read_execution_runner.py)

### Step 6: Shaping And Follow-Up Support
Once the contribution result exists, current follow-up contracts should work normally.

Supported first-slice follow-ups:

1. restrictive projection
2. top-n only
3. scale-only where meaningful

Primary likely files:

1. [memory.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/memory.py)
2. [shaping_policy.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/shaping_policy.py)
3. [response_shaper.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/response_shaper.py)
4. [transform_last.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/transform_last.py)

### Step 7: Quality And Safety Rules
Quality gates must reject:

1. wrong grain
2. wrong metric basis
3. missing contribution-share output
4. contribution-share values inconsistent with the base metric when the metric remains visible
5. silent widening into deferred grouping variants

Primary likely files:

1. [quality_gate.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/quality_gate.py)

## Implementation Order
Recommended exact order:

1. ontology additions
2. capability metadata additions
3. targeted unit tests for ontology/metadata semantics
4. class-contract representation
5. resolver support
6. deterministic contribution helper
7. shaping/follow-up support
8. quality checks
9. replay asset implementation

## Test And Evidence Plan

### A. Before Runtime Coding
Already required and completed:

1. candidate approval review
2. ontology planning
3. metadata planning
4. variation matrix
5. replay design
6. browser/manual golden design

### B. During Implementation
Required targeted tests:

1. ontology normalization coverage
2. capability registry coverage
3. resolver constraint coverage
4. contribution-share helper coverage
5. memory follow-up coverage
6. shaping/projection coverage
7. quality gate coverage

### C. After Implementation
Required reruns:

1. full `contribution_share` suite
2. `core_read`
3. `multiturn_context` if follow-up behavior changed
4. `transform_followup` if last-result transform behavior changed
5. standing browser smoke pack

## Acceptance Rule
The first slice is acceptable only when:

1. the implementation stays inside the approved first slice
2. targeted tests are green
3. new-class replay is green
4. impacted existing suites are green
5. deferred group-share variants remain deferred and documented, not half-implemented
