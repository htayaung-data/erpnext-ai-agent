# Qwen ERP Governed Scope Coverage Round 3 Phase 4 Gap Priority

Status: active research note
Date: 2026-04-13
Scope: Round 3 Phase 4 gap classification and priority for the cross-layer alignment targets proven in Round 3

## 1. Purpose

This note turns the Round 3 evidence into a practical priority map.

It answers:

1. which Round 3 gaps are true blockers or near-blockers for current Phase `3.3`
2. which gaps are real but belong to later governed scope expansion
3. which gaps are alignment fixes versus activation expansions
4. which surfaces are strong enough to preserve as reference seams
5. what should happen before any new implementation starts

This note is about sequencing with honesty.

It should stop us from mixing:

1. current Phase `3.3` completion work
2. broader governed scope expansion
3. future ambiguity generalization

## 2. Evidence Basis

This note is based on:

1. [qwen_erp_governed_scope_coverage_round3_phase1_frontdoor_inventory_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round3_phase1_frontdoor_inventory_2026-04-13.md)
2. [qwen_erp_governed_scope_coverage_round3_phase2_runtime_seam_mapping_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round3_phase2_runtime_seam_mapping_2026-04-13.md)
3. [qwen_erp_governed_scope_coverage_round3_phase3_behavior_truthing_2026-04-13.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_governed_scope_coverage_round3_phase3_behavior_truthing_2026-04-13.md)
4. [qwen_erp_phase_implementation_roadmap_2026-04-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase_implementation_roadmap_2026-04-04.md)
5. [qwen_erp_phase3_composite_governed_artifact_design_2026-04-10.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase3_composite_governed_artifact_design_2026-04-10.md)

## 3. Gap Taxonomy

Round 3 gaps fall into five real categories.

### 3.1 Activation Narrowness

The system already has:

1. vocabulary suppor
2. typed slots
3. sometimes typed contracts

but the active policy or semantic route is still narrow.

### 3.2 Front-Door / Runtime Misalignmen

A surface exists in runtime, but the front door routes the user into the wrong family or no family.

This is more serious than simple absence.

### 3.3 Mixed Runtime Authority

The seam works, but ownership is still split across:

1. metadata
2. typed contracts
3. direct Python branching

### 3.4 Specialized Path Versus Shared Family Path Spli

A surface exists in one specialized runtime area, but not as a strong generic governed family.

### 3.5 Clarification Breadth Deb

The clarification architecture exists, but its active reason types or activation breadth are still too narrow.

## 4. Gap Classification

### 4.1 G1: Purchase Invoice Is Runtime-Real But Front-Door-Misaligned

Observed truth:

1. explicit purchase-invoice detail resolution works
2. generic `show me purchase invoices` currently routes into the sales-invoice path
3. this is a proven wrong-family behavior, not a speculative concern

Root cause class:

1. front-door / runtime misalignmen
2. mixed runtime authority

Priority reading:

1. highest-priority Round 3 alignment issue
2. best candidate for bounded Phase `3.3`-adjacent implementation
3. should be solved by aligning current contracts and metadata, not by adding another one-off purchase-invoice path

### 4.2 G2: Supplier And Item Direct Navigation Are Contract-Ready But Policy-Inactive

Observed truth:

1. supplier/item alias vocabulary already exists
2. slot inference already recognizes those grains
3. typed resolution still fails closed as `unsupported_grain`
4. supplier front-door deterministic lookup stayed inactive in proof

Root cause class:

1. activation narrowness

Priority reading:

1. real gap
2. not a current Phase `3.3` blocker
3. should not be smuggled into `3.3` as a convenience expansion
4. belongs to the next governed scope expansion chapter after current `3.3` closure

### 4.3 G3: Entity Detail Execution Still Uses Mixed Branching

Observed truth:

1. entity detail is a real lane
2. explicit identifier resolution is real
3. document and master-entity detail dispatch still branch directly by `entity_type`
4. customer consumes the stronger typed lookup seam more than supplier/item

Root cause class:

1. mixed runtime authority

Priority reading:

1. near-blocker for broad later expansion
2. not an immediate behavior emergency
3. should be reduced gradually when we align existing seams, not via large refactor-first work

### 4.4 G4: Payment Entry Is Present But Still Specialized

Observed truth:

1. metadata capability exists
2. specialized finance/collections support exists
3. generic front-door interpretation for payment-entry navigation remained inactive

Root cause class:

1. specialized path versus shared family spli
2. activation narrowness

Priority reading:

1. importan
2. but not ready to be treated as a current Phase `3.3` implementation targe
3. first needs an ownership decision about which family should own i

### 4.5 G5: Clarification Is Strong In Architecture But Narrow In Breadth

Observed truth:

1. clarification contracts exis
2. artifact-boundary clarification works
3. evidence-boundary behavior works
4. active reason coverage is still narrow

Root cause class:

1. clarification breadth deb

Priority reading:

1. medium-to-high priority design deb
2. should be extended through the current typed clarification layer
3. should not be solved by phrase-specific “delivered/received” fixes
4. can be expanded incrementally alongside later scope activation

## 5. Strong Round 3 Assets To Preserve

Before focusing only on gaps, Round 3 also proved important assets that should be preserved.

### 5.1 Customer Direct Lookup Is A Strong Reference Surface

It now has:

1. front-door interpretation
2. typed lookup slots
3. typed entity-reference resolution
4. active tests
5. rendering behavior

This is the cleanest current direct-navigation reference seam.

### 5.2 Evidence Boundary Behavior Is Strong

The current system already does something enterprise-correct:

1. it can answer from real evidence when the artifact proves enough
2. it can stop and clarify when the basis is missing
3. it can block overclaiming when the current artifact does not prove the requested fac

This seam should be reused, not replaced.

### 5.3 Typed Lookup And Clarification Contracts Already Exis

Round 3 confirmed that the system already has strong contract assets:

1. fresh-query interpretation contrac
2. entity-reference resolution contrac
3. entity-detail evidence request contrac
4. clarification fields inside typed contracts

This matters because future work should align and activate these, not reinvent them.

## 6. Priority By Roadmap Stage

### 6.1 For Current Phase `3.3`

Current practical decision:

1. keep Phase `3.3` focused on bounded alignment, not broad governed scope expansion

That means:

1. G1 purchase-invoice front-door/runtime alignment is the only clear Round 3 gap that is a strong candidate for current bounded implementation
2. G3 mixed entity-detail branching should be monitored while implementing, but not turned into a broad refactor program in this slice
3. G2 supplier/item activation should stay deferred from current `3.3`
4. G4 payment entry should stay deferred from current `3.3`
5. G5 clarification breadth should be recorded and designed, but not exploded into all-family implementation in this slice

Reason:

1. current Phase `3.3` is still about safe bounded alignment and continuity quality
2. supplier/item/payment-entry activation would widen governed scope, not just align existing seams
3. widening now would mix completion work and expansion work in a risky way

### 6.2 For The Next Governed Scope Expansion Chapter

After current Phase `3.3` is truly closed, the next expansion chapter should prioritize:

1. G2 supplier/item direct navigation activation
2. G4 payment entry ownership and activation
3. G5 broader typed clarification activation
4. gradual reduction of G3 mixed entity-detail branching

This order matters.

Do not start by activating every new grain at once.

Start with the grains or finance surfaces that already have:

1. approved source authority
2. clear family ownership
3. typed contracts ready to carry them safely

## 7. Blocker / Near-Blocker / Monitor View

### 7.1 For Current Phase `3.3`

`blocker`

1. none proven as a universal `3.3` blocker

`near_blocker`

1. G1 purchase-invoice misrouting
2. G3 mixed entity-detail branching

`monitor`

1. G2 supplier/item policy inactivity
2. G4 payment entry partial activation
3. G5 clarification breadth deb

### 7.2 For The Next Expansion Chapter

`blocker`

1. G2 supplier/item activation narrowness
2. G4 payment-entry ownership ambiguity

`near_blocker`

1. G3 mixed entity-detail branching
2. G5 clarification breadth deb

`monitor`

1. additional future grains beyond the current Round 3 scope

## 8. Main Enterprise Recommendation

Round 3 now supports one clear enterprise recommendation:

1. finish current Phase `3.3` with bounded alignment work only
2. do not widen governed scope during `3.3` just because alias vocabulary already exists
3. treat purchase invoice as the highest-value current alignment issue
4. treat supplier/item/payment-entry as the first candidates for the next explicit governed scope expansion chapter
5. expand ambiguity handling through the current typed clarification layer, not through phrase-specific repairs

## 9. What Should Happen Nex

The next safe step after this note is Round 3 Phase 5.

Round 3 Phase 5 should produce the bounded design decision:

1. what exact implementation belongs inside current `3.3`
2. what exact work is explicitly deferred to later scope expansion
3. what typed contract and metadata changes should happen firs
4. what must remain untouched to avoid architecture drif

That design note should be implementation-facing, not just diagnostic.
