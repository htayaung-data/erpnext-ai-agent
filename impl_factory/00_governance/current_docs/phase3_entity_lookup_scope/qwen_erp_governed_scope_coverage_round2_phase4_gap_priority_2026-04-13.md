# Qwen ERP Governed Scope Coverage Round 2 Phase 4 Gap Priority

Status: active research note  
Date: 2026-04-13  
Scope: Round 2 Phase 4 gap classification and priority for document-navigation, finance-operation, and inventory-operation surfaces

## 1. Purpose

This note turns the Round 2 evidence into a practical priority map.

It answers:

1. what kinds of Round 2 gaps actually exist
2. which are real blockers for the next shared enterprise work
3. which are partial-support cases that need careful expansion
4. which should remain deferred
5. what should come before Round 3 implementation planning

## 2. Evidence Basis

This note is based on:

1. [qwen_erp_governed_scope_coverage_round2_phase1_frontdoor_inventory_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round2_phase1_frontdoor_inventory_2026-04-13.md)
2. [qwen_erp_governed_scope_coverage_round2_phase2_runtime_seam_mapping_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round2_phase2_runtime_seam_mapping_2026-04-13.md)
3. [qwen_erp_governed_scope_coverage_round2_phase3_behavior_truthing_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round2_phase3_behavior_truthing_2026-04-13.md)

## 3. Gap Taxonomy

Round 2 gaps fall into six real categories.

### 3.1 Partial Metadata Activation

A surface has:

1. report presence
2. maybe capability presence

but still lacks:

1. semantic family rule
2. clear family routing
3. or explicit entity-reference activation

### 3.2 Mixed Runtime Authority

A surface works, but the runtime still mixes:

1. shared family seams
2. direct entity/document branches
3. special-case document detail functions

### 3.3 Metadata / Runtime Asymmetry

The surface is stronger in one layer than another.

Possible shapes:

1. metadata richer than runtime
2. runtime richer than metadata

### 3.4 Generic Family Path Versus Specialized Side Path Split

Some capabilities appear in specialized runtime support but not in the main shared family path.

This is different from simple absence.

### 3.5 Missing Entity Navigation Activation

A surface may be available as:

1. document listing
2. analytical family
3. direct identifier detail

but still not as:

1. governed direct entity/reference navigation

### 3.6 Still-Absent Governed Surface

The surface is not found in the current inspected metadata/runtime path strongly enough to be treated as active.

## 4. Gap Classification

### 4.1 G1: Entity Detail For Documents Is Working But Still Mixed

Observed truth:

1. sales invoice, sales order, purchase order, and delivery note detail paths are real
2. targeted tests confirm they work
3. runtime still dispatches by direct `entity_type` branches in `entity_detail.py`

Root cause class:

1. mixed runtime authority

Priority reading:

1. high-priority architecture cleanup item
2. not a "broken behavior" emergency
3. important before broader document-scope expansion

### 4.2 G2: Payment Entry Is A Specialized Partial Path, Not A Shared Family Path

Observed truth:

1. `Payment Entry List` exists in reports
2. `collections_read` exists as a capability
3. payment-entry-related logic exists in specialized collections/KPI code
4. no equivalent strong shared semantic/family/runtime path was found in Round 2 generic family seams

Root cause class:

1. partial metadata activation
2. generic family path versus specialized side path split

Priority reading:

1. high-priority investigation item for later expansion
2. not something to casually claim as already generalized
3. should be treated as a bounded expansion candidate, not as a hidden already-finished path

### 4.3 G3: Purchase Invoice Is Runtime-Richer Than Metadata

Observed truth:

1. purchase invoice did not appear strongly in the front-door/family metadata path
2. purchase invoice detail runtime exists
3. purchase invoice shows up through aging-linked voucher context

Root cause class:

1. metadata / runtime asymmetry

Priority reading:

1. high-priority alignment item
2. this is one of the strongest examples where current layers disagree
3. should be normalized before making wider claims about purchase-document coverage

### 4.4 G4: Direct Navigation / Reference Policy Is Still Much Narrower Than Family Breadth

Observed truth:

1. Round 2 has strong family/runtime coverage for several document and analytical surfaces
2. direct entity-reference policy remains much narrower

Root cause class:

1. missing entity navigation activation

Priority reading:

1. important for later shared expansion
2. not a blocker for accepting current strong family paths as real
3. becomes more important when the program wants broader direct lookup and deictic continuity beyond current grains

### 4.5 G5: Purchase Receipt Is Still Not An Active Governed Surface

Observed truth:

1. it was not found strongly in Round 2 metadata inventory
2. it was not found as a shared runtime path
3. it was not verified in behavior truthing

Root cause class:

1. still-absent governed surface

Priority reading:

1. defer as not-yet-activated
2. do not stretch current runtime to imply it is already supported

### 4.6 G6: Journal Entry Is Still Not An Active Governed Surface

Observed truth:

1. it was not found strongly in the current inspected metadata path
2. it was not found as a shared runtime path
3. it was not verified in behavior truthing

Root cause class:

1. still-absent governed surface

Priority reading:

1. defer as not-yet-activated
2. do not widen current scope claims to include it

## 5. Strong Round 2 Assets To Preserve

Before focusing only on gaps, Round 2 also proves important strengths that should be preserved as reference implementations.

### 5.1 Delivery Note Is A Strong Reference Surface

It now shows:

1. semantic routing
2. shared family adaptation
3. shared family rendering
4. follow-up handling
5. detail drilldown
6. evidence-question support

This is one of the best Round 2 examples of how a document surface should mature.

### 5.2 Inventory Snapshot Is A Strong Shared Family Surface

Both item and warehouse inventory paths are already strong and verified enough to be treated as active family-level support.

### 5.3 AR/AP Aging Is A Strong Shared Family Surface

This family already shows:

1. shared semantic routing
2. shared family execution
3. explicit clarification behavior
4. verified tests

This is another good reference shape.

## 6. Priority By Next Research / Design Stage

### 6.1 Highest Priority

1. G1: mixed authority in document entity detail
2. G2: payment entry partial activation
3. G3: purchase invoice metadata/runtime asymmetry

Reason:

These three are the most important shared-design issues uncovered in Round 2.

They are more important than chasing fully absent scopes, because they directly affect how later expansion should be designed.

### 6.2 Medium Priority

1. G4: widen direct navigation/reference policy only after alignment design is ready

Reason:

This matters, but it should follow the shared-seam design rather than happen as isolated activation.

### 6.3 Deferred

1. G5: purchase receipt
2. G6: journal entry

Reason:

Current evidence does not support treating these as near-term hidden wins.

## 7. Practical Recommendation Before Round 3

Round 2 now supports a clear practical recommendation:

1. do not spend the next chapter trying to activate every missing Round 2 surface at once
2. first align the mixed and asymmetric surfaces already partly present
3. use those aligned surfaces to define the safer shared expansion design in Round 3

That means the next design attention should center on:

1. document-detail seam generalization
2. payment-entry activation policy
3. purchase-invoice alignment

not on:

1. turning on every absent document/entity type immediately

## 8. Current Status Statement

Round 2 Phase 4 now has enough evidence to support priority decisions.

Current status:

1. Round 2 revealed real strong family surfaces
2. the main problems are uneven activation and mixed seams, not lack of all infrastructure
3. payment entry and purchase invoice are the most important partial-scope findings
4. purchase receipt and journal entry should remain deferred for now
