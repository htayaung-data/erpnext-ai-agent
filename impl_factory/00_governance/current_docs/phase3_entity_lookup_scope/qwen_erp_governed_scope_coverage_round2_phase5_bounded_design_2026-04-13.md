# Qwen ERP Governed Scope Coverage Round 2 Phase 5 Bounded Design

Status: active design note
Date: 2026-04-13
Scope: bounded design for the next safe Round 2 expansion and alignment chapter after the completed Round 2 research

## 1. Purpose

This note turns the completed Round 2 research into a bounded design recommendation.

It is not a universal ERP expansion blueprint.

It is a practical design for the next safe chapter after Round 2 established:

1. stronger document family coverage than first expected
2. stronger inventory and aging family maturity than first expected
3. mixed authority in document entity detail
4. partial activation for payment entry
5. metadata/runtime asymmetry for purchase invoice

The goal is:

1. reuse the current governed ecosystem
2. avoid a parallel architecture
3. align uneven layers before widening more surface area
4. preserve the already-strong Round 2 families as reference implementations

## 2. Executive Decision

The next safe chapter should not begin by activating every missing Round 2 scope.

It should begin by aligning the most important mixed and asymmetric Round 2 surfaces:

1. document entity detail
2. purchase invoice
3. payment entry

Then, only after that alignment is complete:

1. decide whether payment entry should join the generic family path, stay specialized, or have a bounded hybrid activation
2. decide whether purchase-document breadth should expand further
3. keep purchase receipt and journal entry deferred until there is real evidence and approved ownership

This is the enterprise-safe move because:

1. it strengthens shared seams before widening breadth
2. it reduces disagreement between metadata and runtime
3. it prevents support claims from getting ahead of actual activation
4. it avoids repeating the partial-activation pattern already exposed by Round 2

## 3. What To Keep

Round 2 proved that several important pieces are already strong and should be preserved.

### 3.1 Keep The Shared Family Runtime For Strong Round 2 Families

Keep the current shared family path for:

1. transaction listing
2. aging
3. inventory snapsho
4. ranking
5. trend

Reason:

1. these are not speculative seams
2. they already have strong metadata, runtime, and test evidence
3. they should be treated as reference surfaces, not as redesign targets

### 3.2 Keep Follow-Up Boundary And Local Family Follow-Up

Keep:

1. `FollowUpBoundaryContract`
2. family-level local follow-up refinemen
3. governed requery when the continuation exceeds current artifact authority

Reason:

1. Round 2 did not reveal a continuation architecture gap for these strong families
2. the main issue is activation alignment, not continuation absence

### 3.3 Keep Document Identifier Detail Ownership In The Entity-Detail Lane

Keep:

1. document detail ownership in `entity_detail`
2. direct identifier drilldown as a valid owned path

Reason:

1. the current problem is mixed implementation shape inside the lane
2. the current problem is not that document detail belongs to the wrong lane

## 4. What To Align Nex

## 4.1 Align Document Entity Detail To A Stronger Shared Dispatch Contrac

Current state:

1. document detail works
2. tests prove it works
3. but `entity_detail.py` still dispatches through direct `entity_type` branching

Recommended move:

1. keep the entity-detail lane
2. keep exact identifier drilldown
3. replace direct document-branch expansion pressure with a stronger shared document-detail dispatch seam

Practical meaning:

1. sales invoice
2. sales order
3. purchase order
4. delivery note
5. purchase invoice

should all remain supported, but the path should become more policy-driven and less branch-driven over time.

### 4.2 Align Purchase Invoice Across Metadata And Runtime

Current state:

1. purchase invoice detail exists in runtime
2. purchase invoice appears in aging-linked voucher contex
3. purchase invoice is weak in current front-door/family metadata inventory

Recommended move:

1. do not widen purchase invoice casually everywhere at once
2. first make the support status consistent across metadata and runtime
3. decide which governed ask shapes purchase invoice officially owns

Practical meaning:

1. if purchase invoice detail is a real approved path, metadata should reflect tha
2. if purchase invoice listing or analytical behavior is not yet approved, do not imply it by acciden

### 4.3 Decide Payment Entry Ownership Explicitly

Current state:

1. payment entry exists in report and capability layers
2. payment entry logic exists in specialized collections/KPI suppor
3. payment entry does not currently behave like a strong generic family path

Recommended move:

Make an explicit ownership decision before any activation work:

1. should payment entry become a transaction-listing family member
2. should payment entry remain a collections-owned specialized surface
3. or should it have a bounded two-surface model

Important rule:

1. do not activate payment entry in semantic metadata first and hope the runtime shape catches up later

That would recreate the same partial-activation problem already identified in Round 2.

## 5. What Not To Generalize Ye

### 5.1 Do Not Activate Purchase Receipt Just Because It Sounds Related

Round 2 did not prove:

1. metadata strength
2. runtime strength
3. behavior truth

for purchase receipt.

So it should remain deferred.

### 5.2 Do Not Activate Journal Entry Just Because It Is Core ERP

The same rule applies.

Business importance alone is not enough.

Activation must follow:

1. declared metadata
2. shared runtime ownership
3. bounded truthing

### 5.3 Do Not Collapse Specialized Collections Logic Into The Generic Family Path Prematurely

Payment entry touches collections behavior and may not fit a naïve listing pattern.

So the next design step should be:

1. explicit ownership decision firs
2. activation second

not:

1. force-fit it into a generic lane because the report exists

## 6. Recommended Contract And Metadata Direction

## 6.1 Contract Direction

No brand-new top-level architecture is required for the next bounded chapter.

Reuse:

1. `FreshQueryInterpretationContract`
2. semantic resolution contracts
3. normalized family artifact/render contracts
4. `EntityReferenceResolutionContract`
5. `EntityDetailEvidenceRequestContract`
6. `FollowUpBoundaryContract`

Allowed bounded extension:

1. strengthen document-detail dispatch typing if current entity-detail branching cannot be reduced without i
2. add bounded activation metadata for approved purchase-invoice support if the project decides that support is official
3. add bounded payment-entry ownership metadata only after the ownership model is chosen

## 6.2 Metadata Direction

For any Round 2 surface to be declared as newly active, add the full governed set together:

1. semantic family rule
2. capability mapping
3. report/family mapping
4. entity reference policy if direct navigation is part of the approved surface
5. follow-up/continuation-safe ownership if the family supports i

Important rule:

1. no partial activation

Round 2 proved that partial activation creates confusion and design debt.

## 7. Recommended Implementation Order After Research Closure

### 7.1 Step A: Document Detail Alignmen

Bounded scope:

1. reduce mixed branching in document entity detail
2. preserve all current strong document detail behaviors
3. avoid breaking evidence-follow-up behavior already proven by tests

Acceptance goal:

1. stronger shared dispatch shape for document detail
2. no regression in sales invoice, sales order, purchase order, or delivery note detail behavior

### 7.2 Step B: Purchase Invoice Alignmen

Bounded scope:

1. decide official supported purchase-invoice ask shapes
2. align metadata and runtime accordingly
3. keep unsupported shapes fail-closed

Acceptance goal:

1. purchase invoice support status becomes consistent across layers

### 7.3 Step C: Payment Entry Ownership Decision And Activation

Bounded scope:

1. classify payment entry as generic family surface, specialized collections surface, or bounded hybrid
2. activate only the approved path
3. add truthing for the selected path

Acceptance goal:

1. payment entry is no longer a "half-visible" surface

### 7.4 Step D: Re-evaluate Broader Document Expansion

Only after Steps A to C should the team revisit:

1. purchase receip
2. journal entry
3. broader direct navigation for document grains

## 8. Why This Is The Right Bounded Move

This Round 2 design is safer than broad activation because:

1. it starts from already-proven strong surfaces
2. it fixes layer disagreement before adding more breadth
3. it preserves the existing architecture instead of inventing a new one
4. it uses the research evidence directly

In simple terms:

1. do not widen firs
2. align firs
3. then widen safely

## 9. Current Status Statemen

Round 2 now supports a practical bounded design conclusion.

Current status:

1. Round 2 research is strong enough to guide the next design chapter
2. the next safe work is alignment, not broad activation
3. the highest-value Round 2 design targets are document entity detail, purchase invoice, and payment entry
4. purchase receipt and journal entry should remain deferred until a later evidence-backed chapter
