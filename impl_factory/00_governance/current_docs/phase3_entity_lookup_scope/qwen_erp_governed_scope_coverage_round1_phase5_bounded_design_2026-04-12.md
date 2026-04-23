# Qwen ERP Governed Scope Coverage Round 1 Phase 5 Bounded Design

Status: active design note  
Date: 2026-04-12  
Scope: bounded design for the next safe Round 1 expansion chapter after current Phase `3.3` closure

## 1. Purpose

This note defines the next safe design step after the current customer-scoped Phase `3.3` work is finished.

It is not a universal ERP navigation redesign.

It is a bounded design for Round 1 expansion based on the completed research:

1. Phase 1 inventory
2. Phase 2 runtime seam mapping
3. Phase 3 behavior truthing
4. Phase 4 gap priority

The design goal is:

1. reuse the current governed ecosystem
2. avoid a parallel architecture
3. reduce customer-weighted downstream lane shape
4. prepare safe activation of the next approved grain

## 2. Executive Decision

The next safe chapter should not begin by adding supplier/item metadata only.

The next safe chapter should begin by generalizing the current direct master-data lane shape while preserving the existing customer path.

Then:

1. activate supplier if a real governed source route is approved
2. decide item/product direct-navigation ownership before activation

This keeps the project enterprise-grade because:

1. contract seams stay stable
2. metadata stays authoritative
3. runtime gains shared behavior before breadth
4. unsupported grains still fail closed

## 3. What To Keep

The current ecosystem already has important pieces that should be preserved.

### 3.1 Keep The Existing Front-Door And Intent Model

Keep:

1. `master_data_lookup` as the front-door intent class for direct directory / candidate-resolution asks
2. `entity_detail` as the lane for profile/detail asks
3. `FollowUpBoundaryContract` and current breakout behavior

Reason:

1. the current problem is not that the project lacks intent structure
2. the problem is uneven downstream activation and generalization

### 3.2 Keep The Existing Typed Lookup Slots

Keep the current typed slots already being used through `FreshQueryInterpretationContract.extracted_slots`:

1. `entity_grain`
2. `lookup_mode`
3. `lookup_projection`
4. `lookup_search_text`
5. `lookup_limit`

Reason:

1. these slots are already sufficient for the current direct-navigation family shape
2. adding a brand-new top-level contract is not necessary for the next bounded chapter

### 3.3 Keep `EntityReferenceResolutionContract`

Keep:

1. the existing `EntityReferenceResolutionContract`
2. the current shared `entity_reference_resolution.py` seam

Reason:

1. this is already one of the strongest shared seams in the current system
2. it is the right place for governed candidate resolution

### 3.4 Keep Customer Master As The Reference Implementation

Keep:

1. `customer_master_list`
2. `customer_master_read`
3. `Customer Master List`

Reason:

1. this is the current proven direct-navigation slice
2. it should be treated as the reference shape to generalize from, not as something to discard

## 4. What To Generalize

### 4.1 Generalize The Direct Master-Data Family Lane

Current state:

1. customer has a dedicated family adapter and renderer
2. supplier and item/product do not

Recommended change:

1. extract the shared shape from the customer direct master-data lane
2. make the adapter/renderer metadata-driven where possible
3. keep grain-specific activation in metadata, not in copied Python branches

Practical meaning:

1. customer remains the first active family
2. supplier later plugs into the same generalized lane shape
3. item/product only plugs in once ownership is approved

### 4.2 Generalize Directory Rendering Policy

The next shared lane should support:

1. names-only lists
2. candidate-resolution results
3. standard directory table projection
4. selected-column projection

This behavior already exists for customer.

The design task is:

1. move the shape into a shared governed rendering seam
2. keep family-specific columns and labels in metadata

### 4.3 Generalize Detail Handoff To Use Active Grain Policy

Current state:

1. customer partial-name drilldown can use governed resolution
2. supplier and item still rely on direct grain branches in `entity_detail.py`

Recommended change:

1. make named-entity handoff prefer active governed entity-reference policy
2. keep exact identifier/document resolution where appropriate
3. reduce direct grain branching for master-data grains

Important boundary:

1. do not break document identifier drilldown for invoice/order/delivery types
2. this chapter is about master-data grain cleanup, not document detail redesign

## 5. What Not To Generalize Yet

### 5.1 Do Not Create A Universal ERP Entity Resolver

Do not build:

1. one global resolver for every ERP doctype
2. one giant metadata table for all entities at once
3. automatic activation for any grain merely because data exists in ERP

Reason:

1. that would jump beyond the bounded Round 1 evidence

### 5.2 Do Not Force Item/Product Into The Customer Pattern Without A Policy Decision

Round 1 proved:

1. product wording already routes into adjacent governed inventory/product families

So before item/product direct-navigation activation, we need an explicit policy decision:

1. which ask shapes should remain owned by inventory/product-performance families
2. which ask shapes should move into a direct directory lane

### 5.3 Do Not Move Profile Requests Into Deterministic Family-Surface Fallback

Keep:

1. profile/detail asks in the entity-detail lane

Reason:

1. that is already the intended ownership boundary
2. the cleanup target is grain branching inside that lane, not lane collapse

## 6. Recommended Contract And Metadata Changes

### 6.1 Contract Changes

No new top-level contract family is required for the next bounded chapter.

Reuse:

1. `FreshQueryInterpretationContract`
2. `EntityReferenceResolutionContract`
3. `EntityDetailEvidenceRequestContract`
4. `FollowUpBoundaryContract`
5. normalized family artifact/render contracts

Allowed bounded extension:

1. add shared metadata-driven rendering configuration for directory families if needed
2. add small typed detail-handoff fields only if an existing contract cannot carry the needed meaning

### 6.2 Metadata Changes

For each newly activated grain, add the full governed set together or not at all:

1. semantic family rule
2. capability
3. report family/report or approved direct query source
4. entity reference policy
5. directory projection metadata if the shared renderer needs it

Important rule:

1. no partial activation that leaves the grain visible to semantic interpretation but without a real governed lane

## 7. Recommended Implementation Order

### 7.1 Step A: Generalize The Current Customer Direct-Navigation Lane

Bounded scope:

1. family adapter shape
2. family renderer shape
3. directory projection behavior
4. customer remains the first active proof slice during refactor

Acceptance goal:

1. customer behavior stays stable
2. runtime shape becomes reusable for another grain

### 7.2 Step B: Reduce Mixed Grain Branching In Entity Detail

Bounded scope:

1. master-data grain named-entity resolution only
2. prefer governed policy-driven resolution where active
3. preserve document identifier drilldown

Acceptance goal:

1. remove the need to keep adding grain-specific branches for future Round 1 grains

### 7.3 Step C: Activate Supplier

Only do this if the governed source route is confirmed and approved.

Activation package should include:

1. supplier semantic family rule
2. supplier capability
3. supplier report family/report or direct query source
4. supplier entity reference policy
5. targeted supplier tests

Acceptance goal:

1. supplier direct directory
2. supplier candidate resolution
3. supplier detail handoff through the shared lane

### 7.4 Step D: Decide Item/Product Direct-Navigation Ownership

Before implementation, decide:

1. which product asks remain in inventory/product-performance lanes
2. whether item/product also deserves a direct directory lane

Only after that decision:

1. add direct item/product activation if approved

## 8. Grain Sequencing Recommendation

Recommended next-grain order:

1. supplier
2. item/product

Reason:

1. supplier is cleaner semantically
2. supplier has less overlap with competing analytical families
3. item/product has a real ownership overlap that should be decided explicitly first

## 9. Verification Design For The Next Chapter

The next implementation chapter should prove behavior in three layers.

### 9.1 Contract-Level

Add or extend tests for:

1. generalized directory family adaptation
2. generalized directory rendering
3. policy-driven entity-reference resolution by active grain

### 9.2 Grain-Level

For supplier first:

1. direct names list
2. candidate resolution
3. profile handoff
4. deictic follow-up from supplier directory/detail context

### 9.3 Boundary-Level

Re-assert:

1. stale customer detail does not trap supplier or item/product asks
2. deictic follow-ups still remain grounded where appropriate
3. unsupported grains still fail closed

## 10. What To Defer

The following should remain outside the next bounded chapter:

1. full ERP-wide entity navigation
2. warehouse, territory, sales person, and other grains beyond Round 1
3. chart/OCR/bilingual expansion
4. broad Phase 4 complex-question expansion tied to unproven navigation surfaces

These should come later, after Round 1 expansion proves the shared direct-navigation lane.

## 11. Phase 5 Conclusion

The next safe design is not:

1. add more keyword paths
2. add supplier metadata only
3. add item metadata only
4. build a new parallel entity-navigation subsystem

The next safe design is:

1. keep the current contracts and runtime ownership model
2. generalize the downstream direct master-data lane shape
3. reduce mixed grain branching in entity detail
4. activate the next approved grain on top of that generalized lane

## 12. Recommended Next Implementation Chapter

Recommended next chapter after current `3.3` closure:

1. Round 1 expansion foundation

Suggested mini-slices:

1. `R1E-1` generalize direct master-data lane shape
2. `R1E-2` clean entity-detail master-data grain resolution
3. `R1E-3` activate supplier
4. `R1E-4` decide and, if approved, activate item/product direct navigation
