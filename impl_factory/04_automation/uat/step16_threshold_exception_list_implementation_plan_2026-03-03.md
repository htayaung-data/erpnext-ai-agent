# Threshold Exception List Implementation Plan

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: controlled implementation plan for the first approved behavioral-class expansion candidate `threshold_exception_list`  
Status: implementation planning approved; governed ontology and capability metadata baseline added; class contract representation, resolver support, deterministic execution/filtering, default shaping/follow-up support, quality-rule tightening, and replay asset implementation added; browser/manual activation not yet started

## Purpose
This document turns the approved expansion candidate into a concrete build sequence.

The goal is to start implementation in an enterprise-safe way:

1. metadata and ontology first
2. runtime changes second
3. targeted validation third
4. broader regression and release evidence after that

This is not release approval.  
This is the controlled implementation plan.

## Class Name
- `threshold_exception_list`

## Approved First Slice
The first implementation slice is limited to deterministic exception-style list behavior for:

1. customers with outstanding amount above/below threshold
2. suppliers with outstanding amount above/below threshold
3. suppliers with purchase amount above threshold
4. overdue sales invoices above threshold
5. overdue purchase invoices above threshold
6. items below stock threshold in a warehouse
7. warehouses above/below stock balance threshold

## Explicit Non-Goals For This Implementation
Do not implement in this first slice:

1. causal “why” answers
2. recommendations
3. action advice
4. multi-threshold compound logic
5. fuzzy consultant-style business judgments
6. write/action flows

## Contract Boundary Rules
Implementation must remain inside the established project boundary.

Must not do:

1. prompt-to-report routing maps
2. case-ID hacks
3. runtime business keyword routing
4. hidden fallback logic that cannot be explained by ontology, metadata, or persisted state

Must do:

1. use ontology for comparator/threshold language
2. use capability metadata for supported metrics/grains/comparators
3. keep runtime generic
4. preserve current follow-up and projection contracts

## Implementation Strategy

### Step 1: Governed Ontology Additions
Add only the reviewed first-slice ontology semantics:

1. comparator aliases:
   - above
   - below
   - over
   - under
   - greater than
   - less than
   - at least
   - at most
2. exception language:
   - overdue
   - low stock
   - below minimum stock
3. threshold value expression normalization:
   - plain numbers
   - comma-formatted numbers
   - governed scale expressions like `million` if already supported cleanly

Primary likely files:

1. [ontology_base_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/ontology_base_v1.json)
2. [ontology_normalization.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/ontology_normalization.py)

Current status:

- complete for the approved first slice

### Step 2: Capability Metadata Additions
Declare threshold-ready behavior in governed metadata before runtime logic depends on it.

Required metadata additions:

1. threshold-filterable metrics
2. supported comparators
3. status-based exception support for overdue invoice flows
4. aggregate-row policy for warehouse exceptions
5. exception-safe visible columns

Primary likely files:

1. [capability_registry_overrides_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/capability_registry_overrides_v1.json)
2. [capability_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/capability_registry.py)

Current status:

- complete for the approved first slice

### Step 3: Class Contract Representation
Introduce the class in a controlled, explicit way.

Required:

1. class identity in planning/runtime contract layer
2. approved output modes
3. approved follow-up semantics
4. clarification rules for missing metric/grain/threshold

Primary likely files:

1. [spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/spec_pipeline.py)
2. any relevant contract/planning module used to normalize behavior class

Current status:

- complete for the approved first slice

### Step 4: Resolver Support
Add generic resolver support for threshold exception reads using governed metadata only.

Runtime should:

1. match canonical metric + comparator + grain to threshold-capable reports
2. reject reports that do not support threshold-ready execution for that grain
3. prefer summary-safe paths for finance customer/supplier exceptions
4. prefer invoice-grain paths for overdue invoice exceptions

Primary likely files:

1. [semantic_resolver.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/semantic_resolver.py)
2. [resolver_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/resolver_pipeline.py)

Current status:

- complete for the approved first slice

### Step 5: Execution And Filtering
Implement deterministic threshold filtering without breaking current read behavior.

Rules:

1. source filtering when metadata/report path safely supports it
2. safe deterministic post-filtering only where approved
3. no silent unsupported expansion
4. preserve entity grain

Primary likely files:

1. [read_engine.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/read_engine.py)
2. [read_execution_runner.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/read_execution_runner.py)
3. possibly a new bounded helper module if the logic is large enough to justify one

Current status:

- complete for the approved first slice
- implemented as a bounded policy helper in:
  - [threshold_exception_policy.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/threshold_exception_policy.py)
- wired into the execution loop before shaping so:
  - row filtering is deterministic
  - filtered `_source_table` state is preserved for follow-ups
  - aggregate summary rows are excluded where governed metadata requires it

### Step 6: Shaping And Follow-Up Support
Once the exception list exists, current follow-up contracts should work normally.

Supported first-slice follow-ups:

1. restrictive projection
2. top-n only
3. scale-only where meaningful

Primary likely files:

1. [response_shaper.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/response_shaper.py)
2. [transform_last.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/transform_last.py)
3. [memory.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/memory.py) if active-result follow-up logic needs class-specific generic support

Current status:

- complete for the approved first slice
- implemented through governed `exception_safe_columns` consumption in:
  - [shaping_policy.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/shaping_policy.py)
- default first-turn exception outputs now use report-declared safe columns
- existing projection and scale follow-up behavior remains on the standard filtered-result path

### Step 7: Quality And Safety Rules
Quality gates must reject:

1. wrong grain
2. wrong comparator direction
3. wrong threshold handling
4. unsupported report fallback pretending to satisfy the class

Primary likely files:

1. [quality_gate.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/quality_gate.py)

Current status:

- complete for the approved first slice
- threshold exception outputs now fail deterministically when:
  - threshold rule metadata was not applied
  - primary dimension does not align with the governed report grain
  - returned rows do not satisfy the requested comparator
  - aggregate summary rows leak into the exception result
  - overdue exception rows are not actually overdue

## Implementation Order
Recommended exact order:

1. ontology additions
2. capability metadata additions
3. targeted unit tests for ontology/metadata semantics
4. resolver support
5. execution/filtering support
6. shaping/follow-up support
7. quality checks
8. replay asset implementation
9. browser/manual validation

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

1. ontology normalization unit coverage
2. resolver constraint coverage
3. shaping/projection follow-up coverage
4. quality gate rejection coverage for wrong-grain outputs

### C. After Implementation
Required reruns:

1. full `threshold_exception_list` suite
2. `core_read`
3. `multiturn_context` if follow-up logic changes
4. standing browser smoke pack
5. curated `threshold_exception_list` browser/manual golden pack

Current status:

- Step 8 replay asset implementation is complete
- new suite file:
  - [threshold_exception_list.jsonl](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/replay_v7_expanded/threshold_exception_list.jsonl)
- replay manifest wiring is complete:
  - [manifest.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/replay_v7_expanded/manifest.json)
- browser/manual activation remains pending
3. `multiturn_context` if follow-up logic is touched
4. standing browser smoke pack
5. threshold-exception manual golden pack

### D. Milestone Evidence
Before milestone close:

1. refresh release gate if the class is part of the milestone scope
2. confirm finance-critical subflows with Tier 1 rigor

## No-Go Conditions
Stop implementation and return to planning if:

1. metadata cannot cleanly declare threshold-capable report behavior
2. runtime logic starts depending on prompt-specific routing
3. finance and inventory first slice need incompatible semantics
4. follow-up behavior destabilizes current green classes

## Initial Acceptance Criteria For Runtime Slice
The first implementation slice is acceptable only if:

1. base finance customer/supplier threshold cases pass
2. overdue invoice threshold cases pass
3. inventory item and warehouse threshold cases pass
4. projection follow-up works on the active result
5. no wrong-grain fallback passes quality
6. impacted existing suites remain green

## Recommendation
This class is ready to move into controlled runtime implementation planning now.

Best next engineering move:

1. start with ontology and capability metadata changes only
2. do not code execution logic first
3. keep the first slice narrow and deterministic
