# Qwen ERP Governed Scope Coverage Round 3 Phase 5 Bounded Design

Status: active design note
Date: 2026-04-13
Scope: bounded design for the next safe Round 3 implementation chapter after completed Round 3 research

## 1. Purpose

This note turns the completed Round 3 research into one bounded implementation decision.

It is not a general ERP navigation redesign.

It is a practical design that answers:

1. what exact work belongs inside current Phase `3.3`
2. what exact work must be deferred to later governed scope expansion
3. what typed seams should be reused
4. what new metadata or contract changes are actually needed
5. how to avoid architecture drift while fixing real problems

## 2. Executive Decision

The next safe implementation chapter should stay inside current Phase `3.3` and perform one bounded alignment fix:

1. align purchase-invoice generic routing with the already-existing purchase-invoice runtime detail seam

At the same time, the project should explicitly defer from current `3.3`:

1. supplier direct-navigation activation
2. item/product direct-navigation activation
3. payment-entry generic navigation activation
4. broad all-family clarification expansion
5. large entity-detail refactor-first work

This is the enterprise-safe move because:

1. it fixes a proven wrong-family behavior
2. it reuses existing contracts and runtime suppor
3. it does not widen governed scope by stealth
4. it keeps later expansion work cleanly separated

## 3. What To Keep

Round 3 proved that the current ecosystem already has valuable seams that should be preserved.

### 3.1 Keep The Current Front-Door And Fresh-Query Contract Model

Keep:

1. `FreshQueryInterpretationContract`
2. current semantic-resolution metadata model
3. current family/capability/report selection flow

Reason:

Round 3 did not reveal that the front-door contract model is wrong.

It revealed that one current document surface is misaligned inside that model.

### 3.2 Keep The Existing Entity Drilldown Lane

Keep:

1. `detect_entity_drilldown_request(...)`
2. `handle_entity_drilldown_turn(...)`
3. `execute_entity_drilldown(...)`

Reason:

Round 3 proved this lane is real and valuable.

The problem is mixed authority inside the lane, not that the lane should be replaced.

### 3.3 Keep The Current Typed Entity-Reference Contrac

Keep:

1. `EntityReferenceResolutionContract`
2. `entity_reference_resolution.py`
3. current lookup slots:
   1. `entity_grain`
   2. `lookup_mode`
   3. `lookup_projection`
   4. `lookup_search_text`
   5. `lookup_limit`

Reason:

These seams already exist and already fail closed correctly.

The next step is selective activation and alignment, not contract reinvention.

### 3.4 Keep The Current Clarification And Evidence Boundary Layer

Keep:

1. `EntityDetailEvidenceRequestContract`
2. artifact-boundary clarification flow
3. evidence-boundary behavior

Reason:

Round 3 proved this layer already does the right thing when evidence is insufficient.

The issue is breadth, not absence.

## 4. What To Implement Inside Current Phase `3.3`

## 4.1 One Bounded Alignment Slice: Purchase Invoice

Current proven problem:

1. explicit purchase-invoice detail works
2. generic `show me purchase invoices` misroutes into the sales-invoice family

Recommended implementation scope:

1. align metadata and fresh-query interpretation so purchase-invoice asks do not collapse into sales-invoice
2. make the support status explicit and consistent across layers
3. reuse the current document-detail lane rather than inventing a parallel purchase-invoice subsystem

Practical target:

1. if purchase-invoice listing/navigation is approved in the current ecosystem, add the minimum metadata and routing alignment needed for that approved path
2. if only purchase-invoice detail is currently approved, then generic purchase-invoice listing asks should fail closed or clarify, but must no longer misroute to sales invoice

Important rule:

The minimum acceptable outcome is not “support purchase invoice everywhere.”

The minimum acceptable outcome is:

1. no wrong-family routing
2. explicit support status
3. typed, auditable behavior

## 4.2 Small Safety Improvement: Guard Against Wrong-Family Document Collapse

This is still part of the same bounded slice.

Recommended behavior:

1. generic document-type asks should not silently collapse into a different document family when the requested family is not actually active

This is not a new family-expansion chapter.

It is a shared alignment guard that protects business meaning.

## 5. What To Defer From Current Phase `3.3`

## 5.1 Defer Supplier Direct Navigation Activation

Reason:

1. Round 3 proved supplier vocabulary exists
2. but typed policy activation is still absen
3. activating supplier now would widen governed scope, not just align existing behavior

Required later chapter:

1. explicit governed source approval
2. semantic rule activation
3. entity-reference policy activation
4. bounded tests

## 5.2 Defer Item/Product Direct Navigation Activation

Reason:

1. Round 3 proved item/product vocabulary exists
2. but policy activation is still absen
3. item/product also has ownership overlap with inventory and product-performance families

Required later chapter:

1. explicit ownership policy
2. approved activation path
3. bounded tests

## 5.3 Defer Payment Entry Generic Navigation Activation

Reason:

1. Round 3 proved Payment Entry is partial, not absen
2. capability and specialized runtime support already exis
3. but generic family ownership is still unresolved

Required later chapter:

1. ownership decision firs
2. activation second

## 5.4 Defer Broad Clarification Expansion

Reason:

1. clarification architecture already exists
2. broadening it across many families is real work
3. it is not required to fix the current purchase-invoice misrouting issue

Required later chapter:

1. typed ambiguity family expansion
2. later rollout by approved surfaces

## 5.5 Defer Large Entity-Detail Refactor-First Work

Reason:

1. mixed entity-detail branching is real
2. but a large refactor is not required to fix the current highest-value alignment defec
3. doing both at once would raise risk and blur scope

Recommended posture:

1. touch mixed entity-detail code only where needed for the bounded purchase-invoice alignment slice
2. keep broader branch-reduction as a later explicit chapter

## 6. Recommended Contract And Metadata Changes

## 6.1 Contract Direction

No brand-new top-level contract family is needed for the next bounded slice.

Reuse:

1. `FreshQueryInterpretationContract`
2. `EntityReferenceResolutionContract`
3. `EntityDetailEvidenceRequestContract`
4. normalized family artifact/render contracts

Allowed bounded extension:

1. add a narrowly-scoped typed document-family discriminator only if current extracted slots cannot safely distinguish purchase-invoice asks from sales-invoice asks

Important rule:

Do not add a new contract just because the current metadata is incomplete.

Use the smallest typed extension needed.

## 6.2 Metadata Direction

If purchase invoice is approved for generic routing in current scope, add the full governed set together:

1. semantic family-resolution rule
2. capability mapping
3. report/family mapping
4. any required document-type slot mapping

If generic purchase-invoice routing is not yet approved, then instead add the bounded semantic guard that prevents wrong-family routing.

Important rule:

1. no partial activation that only makes the ask “look supported”

## 7. Recommended Implementation Order

### 7.1 Step A: Decide Official Purchase-Invoice Support Status

Before code changes, decide one of two enterprise-safe positions:

1. `approved_generic_path`
   - purchase-invoice generic listing/navigation is approved now
2. `detail_only_for_now`
   - purchase-invoice detail is approved, but generic listing/navigation is not yet approved

This decision should be based on the real existing ecosystem, not convenience.

### 7.2 Step B: Align Fresh-Query Routing With That Decision

If `approved_generic_path`:

1. add the minimum metadata and compiler alignment so purchase-invoice asks route into the correct family

If `detail_only_for_now`:

1. block or clarify generic purchase-invoice listing asks
2. but do not route them into sales invoice

### 7.3 Step C: Add Narrow Regression Coverage

Required regression checks:

1. `show me purchase invoices`
2. `tell me more about ACC-PINV-...`
3. `show me sales invoices`
4. one unrelated strong current path such as customer direct lookup

Acceptance goal:

1. purchase invoice no longer misroutes
2. current sales invoice behavior stays stable
3. customer direct lookup stays stable

## 8. What Not To Do

Do not:

1. widen supplier/item/product activation during this slice
2. activate payment entry casually because the capability exists
3. add phrase-specific branches for `purchase invoice`
4. create a parallel purchase-document router
5. launch a broad clarification redesign during this slice
6. refactor `entity_detail.py` broadly without a bounded reason

## 9. Main Enterprise Recommendation

Round 3 now supports one clean implementation recommendation:

1. treat purchase-invoice routing alignment as the next bounded current-Phase `3.3` implementation targe
2. keep all broader navigation expansion explicitly deferred
3. reuse the contracts and runtime seams already presen
4. add only the minimum metadata and routing changes needed to stop wrong-family behavior

## 10. What Comes After This

After the bounded purchase-invoice alignment slice is complete, the next chapter should be a separate governed scope expansion decision for:

1. supplier direct navigation
2. item/product direct navigation
3. payment-entry ownership and activation
4. broader typed ambiguity expansion

That later chapter should start fresh, not be hidden inside current `3.3`.
