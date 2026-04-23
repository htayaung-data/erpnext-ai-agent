# Qwen ERP Governed Scope Coverage Round 1 Phase 4 Gap Priority

Status: active research note  
Date: 2026-04-12  
Scope: Round 1 Phase 4 gap classification and priority for `customer`, `supplier`, and `item/product`

## 1. Purpose

This note turns the Round 1 evidence into a practical priority map.

It answers:

1. what kinds of gaps actually exist
2. which gaps are blockers for current Phase `3.3`
3. which gaps are blockers for later Round 1 scope expansion
4. which gaps should stay deferred instead of being forced into the current slice

This note is about sequencing, not just diagnosis.

## 2. Evidence Basis

This note is based on:

1. Round 1 Phase 1 front-door and metadata inventory
2. Round 1 Phase 2 runtime seam mapping
3. Round 1 Phase 3 behavior truthing

The evidence now supports strong classification rather than guesswork.

## 3. Gap Taxonomy

Round 1 gaps fall into five real categories.

### 3.1 Missing Metadata Activation

The semantic layer may understand a request, but the grain is not activated by:

1. family rule
2. capability
3. family/report mapping
4. entity reference policy

### 3.2 Missing Downstream Runtime Generalization

Metadata may be partly ready, but the execution lane is not generalized across grains.

Examples:

1. family adaptation
2. family rendering
3. detail handoff

### 3.3 Mixed Authority Runtime Debt

Some runtime seams still mix:

1. shared governed resolution
2. direct grain branching
3. legacy or tactical handling

This is different from missing metadata.

### 3.4 Naming And Taxonomy Unevenness

The same business surface is described differently across seams.

Round 1 example:

1. `item`
2. `product`

### 3.5 Intent Ownership Ambiguity

Some asks can legitimately fit more than one governed family.

Round 1 example:

1. `give me some product names`

That can point toward:

1. direct master-data navigation
2. inventory snapshot
3. product-performance families

This is not always a bug.
Sometimes it is an unresolved policy decision.

## 4. Gap Classification

### 4.1 G1: Supplier Direct Lookup Activation Is Missing

Observed truth:

1. supplier vocabulary exists semantically
2. supplier breakout from stale context works
3. supplier direct lookup does not enter a `master_data_lookup` execution lane

Root cause class:

1. missing metadata activation

Evidence:

1. no `master_supplier_directory` rule
2. no `supplier_master_read`
3. no `supplier_master_list` family/report
4. no supplier entity reference policy

Priority reading:

1. not a blocker for finishing current customer-scoped `3.3`
2. blocker for future supplier direct navigation expansion

### 4.2 G2: Item/Product Direct Lookup Activation Is Missing

Observed truth:

1. item/product vocabulary exists semantically
2. product breakout from stale context works
3. `give me some product names` routes to `inventory_summary` through `Stock Balance`
4. no direct item/product master-data lookup lane is active

Root cause class:

1. missing metadata activation
2. intent ownership ambiguity

Evidence:

1. no `master_item_directory` rule
2. no `item_master_read` or `product_master_read`
3. no direct item/product master family/report
4. product wording is currently absorbed by adjacent governed families

Priority reading:

1. not a blocker for finishing current `3.3`
2. high-priority design question before item/product direct navigation is expanded

### 4.3 G3: Direct Master-Data Adaptation And Rendering Are Customer-Weighted

Observed truth:

1. customer has end-to-end direct lookup rendering
2. supplier and item/product do not

Root cause class:

1. missing downstream runtime generalization

Evidence:

1. dedicated `_build_customer_master_artifact(...)`
2. dedicated `_customer_master_blocks(...)`
3. no equivalent supplier/item direct master-data families in runtime

Priority reading:

1. near-blocker for any Round 1 expansion beyond customer
2. not a blocker for current customer-scoped `3.3` closure

### 4.4 G4: Entity Detail Named-Entity Resolution Still Uses Mixed Grain Branching

Observed truth:

1. customer partial name uses governed entity reference resolution
2. supplier and item still rely on direct branch checks in `entity_detail.py`
3. the same function mixes exact lookups and governed fuzzy resolution

Root cause class:

1. mixed authority runtime debt

Priority reading:

1. near-blocker for enterprise-safe Round 1 expansion
2. should be cleaned before or during broader grain activation
3. should not be widened by adding more grain-specific branches

### 4.5 G5: Item/Product Naming Is Uneven Across Seams

Observed truth:

1. some metadata uses `item`
2. some runtime/business routing uses `product`
3. translation helpers already exist in runtime

Root cause class:

1. naming and taxonomy unevenness

Priority reading:

1. medium priority
2. not the first thing to fix alone
3. should be normalized as part of a bounded expansion design, not as isolated cleanup

### 4.6 G6: Profile Requests Use A Separate Lane From Deterministic Family-Surface Fallback

Observed truth:

1. `tell me more about Ko Nay Lin Mobile Center` does not use deterministic family-surface fallback
2. profile requests are handled through the entity-detail lane

Root cause class:

1. intent ownership by a separate runtime lane

Priority reading:

1. not a defect by itself
2. should not be "fixed" by forcing all profile asks through family-surface fallback
3. only becomes a problem if the entity-detail lane remains grain-branching and hard to generalize

## 5. Priority By Roadmap Stage

### 5.1 For Current Phase `3.3`

Current practical decision:

1. do not pause `3.3` to widen supplier/item scope
2. finish the bounded current `3.3` work on approved current governed scope

Reason:

1. Round 1 evidence does not show supplier/item activation as a hidden easy win inside the current lane
2. widening now would mix seam completion and scope expansion
3. that would create architecture drift

For current `3.3`, the only Round 1 gap that matters directly is:

1. avoid adding more mixed-authority or grain-branching logic while closing the current slice

### 5.2 For The Next Scope Expansion Chapter

The next true expansion chapter should start with these priorities:

1. G3: generalize the direct master-data adaptation/rendering lane
2. G4: reduce mixed grain branching in entity-detail resolution
3. G1: activate supplier only if a real governed source path is approved
4. G2: decide item/product direct navigation policy before activation
5. G5: normalize item/product naming as part of that bounded design

This order matters.

Do not start by simply adding:

1. `master_supplier_directory`
2. `master_item_directory`

without addressing the downstream lane shape.

That would create metadata symmetry without runtime symmetry.

## 6. Blocker / Near-Blocker / Monitor View

### 6.1 For Current Phase `3.3`

`blocker`

1. none newly proven by Round 1

`near_blocker`

1. G4 mixed grain branching in entity detail

`monitor`

1. G1 supplier direct lookup missing
2. G2 item/product direct lookup missing
3. G5 item/product naming unevenness
4. G6 separate profile lane ownership

### 6.2 For The Next Round 1 Expansion Chapter

`blocker`

1. G3 missing generalized downstream lane

`near_blocker`

1. G4 mixed grain branching in entity detail
2. G2 unresolved item/product direct navigation policy

`monitor`

1. G1 supplier activation once governed source is confirmed
2. G5 item/product naming unevenness
3. G6 profile lane ownership

## 7. What Should Be Deferred

The following should remain deferred and should not be forced into the next immediate implementation slice:

1. universal ERP-wide entity navigation in one jump
2. activation of every ERP doctype under one generic resolver
3. replacing all existing families with a brand-new parallel architecture
4. phrase-driven support for unseen asks just to make browser prompts look better

Reason:

1. Round 1 already proved that the safer path is bounded grain expansion with shared-lane hardening

## 8. Recommended Sequencing

### 8.1 Immediate

1. finish current Phase `3.3` on the approved current governed scope

### 8.2 Next Design Chapter

1. start a bounded Round 1 expansion design note
2. goal: reuse the existing `master_data_lookup`, entity-reference, entity-detail, follow-up, and metadata ecosystem
3. do not invent a parallel architecture

### 8.3 First Expansion Implementation Slice

1. generalize the direct master-data lane shape first
2. then activate the next approved grain

### 8.4 Grain Order Recommendation

Recommended order:

1. supplier
2. item/product

Reason:

1. supplier is more semantically straightforward
2. item/product has a real ownership overlap with inventory and product-performance families
3. that overlap deserves an explicit governed policy decision before activation

## 9. Phase 4 Conclusion

Round 1 Phase 4 leads to one clear decision:

1. current `3.3` should finish on current approved scope
2. Round 1 expansion should not begin by adding supplier/item metadata only
3. the next safe chapter must first address the customer-weighted downstream lane shape

This keeps the project enterprise-grade because it avoids:

1. fake symmetry
2. one-off grain rescue
3. metadata activation without real runtime parity

## 10. Next Step

Next step:

1. Round 1, Phase 5
2. write the bounded design note for the next safe expansion chapter

That note should define:

1. what to keep
2. what to generalize
3. what to defer
4. what new activation sequence to use
