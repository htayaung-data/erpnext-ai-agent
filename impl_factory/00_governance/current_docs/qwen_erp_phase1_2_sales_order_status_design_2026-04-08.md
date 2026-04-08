# Qwen ERP Phase 1.2 Sales Order Status Design

Status: proposed active design note  
Date: 2026-04-08  
Scope: detailed implementation plan for Phase 1, Mini-phase 1.2

## 1. Executive Decision

Phase 1.2 should start with a governed `Sales Order` status surface, not a broad order-lifecycle platform.

The first implementation must stay:

1. read-only
2. metadata-first
3. status-authority driven
4. bounded to real ERP order facts
5. small enough to verify with the existing enterprise gate

This means the first target is:

1. governed `Sales Order` listing
2. status-aware filtering and date-scope handling
3. governed `Sales Order` detail
4. bounded order-status follow-up from grounded order artifacts

This phase should not start with:

1. cross-document reconciliation across quotation, sales order, delivery note, and invoice
2. payment-terms reasoning as a primary path
3. trend/reporting expansion as the entry slice
4. workflow-write or approval actions
5. delivery-proof by inference from downstream documents unless the order artifact itself is insufficient and a later bounded slice explicitly approves that widening

## 2. What Phase 1.1 Proved

Phase 1.1 gives strong implementation guidance for Phase 1.2.

What worked and should be reused:

1. start from the narrowest real operational ask
2. reuse the existing `transaction_listing` family before inventing a new family
3. introduce a direct-query document-listing report before trends
4. reuse `entity_detail` instead of inventing a new drilldown lane
5. keep follow-up continuity grounded on typed artifacts, not raw message text
6. add browser/UAT checkpoints before calling a slice complete
7. convert important behavior into release-gated smokes only after the authority seam is stable

What went wrong in Phase 1.1 and must not repeat:

1. letting `latest` drift into current-day scope instead of structural limit semantics
2. allowing a new domain to diverge from existing shared listing behavior
3. patching phrase-level behavior before checking whether the old governed contract already existed
4. mixing too much cleanup with expansion before the bounded checkpoint was done

## 3. Enterprise Guideline Constraints For 1.2

Phase 1.2 must obey the active enterprise guide:

1. contract first
2. metadata owns business policy
3. compiler enforces deterministically
4. fail closed when evidence is insufficient
5. no keyword routing
6. no single-case prompt fixes
7. two-layer verification is required:
   - fast deterministic contract tests
   - live/site verification where state matters
8. expand only after the previous chapter is closed
9. stop when the stop rule is met

This means `Sales Order Status` must be built as:

1. governed metadata plus typed contract expansion
2. bounded runtime reuse
3. explicit deferrals for anything broader than status visibility and status follow-up

## 4. Current ERP And Repo Findings

The live ERP and codebase support a narrow but valuable `Sales Order` status chapter.

### 4.1 Live ERP surface

The `Sales Order` doctype already exposes the right operational status fields:

1. `status`
2. `docstatus`
3. `transaction_date`
4. `delivery_date`
5. `grand_total`
6. `total_qty`
7. `per_delivered`
8. `per_billed`
9. `billing_status`

Live data already shows meaningful operational variation, including:

1. `Draft`
2. `To Deliver and Bill`
3. `To Bill`

So this is a real business surface, not speculative coverage.

### 4.2 Standard ERP report surface

ERP already exposes standard selling reports relevant to later expansion:

1. `Sales Order Analysis`
2. `Sales Order Trends`
3. `Payment Terms Status for Sales Order`

These are important, but they should not be Phase `1.2` entry points.

### 4.3 Current assistant surface

The governed metadata currently has no mature `Sales Order` capability surface.

What already exists and should be reused:

1. generic direct-query listing infrastructure
2. shared `transaction_listing` family
3. shared `entity_detail` family
4. shared continuation and follow-up contracts
5. shared browser/UAT and release-gate pattern proven in Phase `1.1`

What does not yet exist:

1. `Sales Order List` report metadata
2. `Sales Order` semantic-resolution entries
3. `Sales Order` status normalization policy
4. `Sales Order` explicit entity-detail support

## 5. Authority Model For Sales Order Status

The first authoritative order-status model must be intentionally narrow.

Primary authority should be:

1. `Sales Order.status`
2. `Sales Order.docstatus`
3. `Sales Order.per_delivered`
4. `Sales Order.per_billed`
5. `Sales Order.delivery_date`

Supporting context may include:

1. `grand_total`
2. `total_qty`
3. `customer`
4. `company`

Deferred authority for later slices only:

1. delivery-note-derived actual shipment proof
2. invoice-derived billing narrative beyond order-level billed percentage
3. payment-terms semantics from specialized reports
4. multi-artifact lifecycle explanation

This means:

1. Phase `1.2` should answer order-status questions from order authority first
2. it should not become a hidden composite engine
3. if users ask beyond order authority, the system should fail closed or defer to a later bounded slice

## 6. Scope For Phase 1.2

### 6.1 In scope

1. latest sales-order listing
2. date-scoped sales-order listing
3. status-filtered sales-order listing
4. submitted-order lifecycle visibility
5. explicit sales-order detail by identifier
6. grounded follow-up from sales-order detail:
   - current status
   - delivered percentage
   - billed percentage
   - planned delivery date
7. contract tests, browser/UAT, and release-gated smokes

### 6.2 Explicitly deferred

1. `Sales Order Trends` as a first-slice entry point
2. `Sales Order Analysis` as the first artifact surface
3. `Payment Terms Status for Sales Order`
4. draft-versus-submitted mixed policy unless a bounded extension is explicitly approved
5. actual-delivery-date answers from downstream documents
6. quotation-to-order or order-to-invoice composite storytelling

## 7. Detailed Mini-Phase Plan

### 7.1 `1.2A` Submitted Sales Order Listing Baseline

Goal:

1. establish the first governed `Sales Order` read surface through the already-proven document-listing pattern

Implementation ownership:

1. metadata:
   - add capability `sales_order_read`
   - add report `Sales Order List`
   - map it to `transaction_listing`
2. runtime:
   - reuse direct-query execution
   - no new family
   - no new lane
3. docs:
   - record scope and stop rule immediately

Recommended first-slice report shape:

1. doctype: `Sales Order`
2. grounding mode: `direct_query`
3. date field: `transaction_date`
4. initial fields:
   - `name`
   - `transaction_date`
   - `customer`
   - `status`
   - `company`
   - `grand_total`
   - `per_delivered`
   - `per_billed`
   - `delivery_date`
   - `docstatus`
5. default order:
   - `transaction_date desc, modified desc`

Policy choice for `1.2A`:

1. start with submitted orders only (`docstatus = 1`)
2. treat draft visibility as a later bounded extension

Why:

1. it mirrors the successful Delivery entry strategy
2. it keeps the first authority surface simple
3. it avoids mixing draft workflow policy into the first checkpoint

Example asks covered:

1. `show me latest 7 sales orders`
2. `show me sales orders with status To Deliver and Bill`
3. `show me submitted sales orders from last month`

Acceptance for `1.2A`:

1. `latest N` means structural limit, not current-day scope
2. status-filtered order listing works through governed metadata
3. summary totals are grounded from list rows only
4. no sales-order-specific keyword routing is introduced

### 7.2 `1.2B` Status Normalization And Date-Scope Enrichment

Goal:

1. make the listing surface trustworthy for real status questions instead of only raw row retrieval

Implementation ownership:

1. metadata:
   - add governed status values and aliases
   - clarify allowed statuses for Phase `1.2`
2. compiler:
   - keep status extraction policy metadata-driven
3. runtime:
   - continue reusing `transaction_listing`

Recommended status set for first governed support:

1. `To Deliver`
2. `To Bill`
3. `To Deliver and Bill`
4. `Completed`
5. `Closed`

Explicitly defer in this slice:

1. broad draft-policy questions if they require special docstatus treatment
2. workflow-state semantics beyond the standard `status` field

Example asks covered:

1. `show sales orders to bill`
2. `show sales orders to deliver last month`
3. `show completed sales orders`

Acceptance for `1.2B`:

1. date-scope and status can coexist without continuation drift
2. month-scoped listing returns the full governed set, not a hidden capped subset
3. browser/UAT confirms the same prompts work outside smoke helpers

### 7.3 `1.2C` Sales Order Detail Drilldown Parity

Goal:

1. make explicit `Sales Order` identifiers behave like invoice and delivery-note drilldown already do

Implementation ownership:

1. entity-detail:
   - extend explicit identifier resolution for `SAL-ORD-...`
   - add governed `Sales Order` detail rendering
2. runtime:
   - reuse the existing entity-drilldown path
   - do not invent a sales-order-only detail lane

Recommended detail payload:

1. order id
2. customer
3. transaction date
4. planned delivery date
5. status
6. grand total
7. total quantity
8. delivered percentage
9. billed percentage
10. item rows

Example asks covered:

1. `tell me more about SAL-ORD-2026-00022`
2. `show details for SAL-ORD-2026-00024`

Acceptance for `1.2C`:

1. fresh-chat explicit identifier goes to order detail, not list/report drift
2. order detail is grounded on the `Sales Order` doctype itself
3. browser/UAT confirms parity with invoice/delivery-note detail behavior

### 7.4 `1.2D` Order-Status Follow-Up From Detail

Goal:

1. answer the most common order-status follow-ups from the grounded order artifact without widening into composite lifecycle analysis

Supported follow-up classes:

1. `is it delivered?`
2. `how much is delivered?`
3. `is it billed?`
4. `how much is billed?`
5. `what is the delivery date?`

Authority rules:

1. delivery-progress answers come from `per_delivered`
2. billing-progress answers come from `per_billed`
3. planned date answers come from `delivery_date`
4. do not answer actual shipment date from order authority alone

This is intentionally different from `1.1D`:

1. `1.1D` needed downstream delivery proof
2. `1.2D` can stay on order authority because the user is asking about order status, not shipment proof

Example asks covered:

1. `is this sales order delivered?`
2. `how much is billed?`
3. `when is delivery due?`

Fail-closed rules:

1. if a user asks for actual delivery event proof from an order, do not guess
2. if they ask for downstream artifact certainty not carried by the order artifact, defer to a later bounded slice

Acceptance for `1.2D`:

1. the follow-up remains anchored to the current sales-order detail artifact
2. no raw text heuristics become hidden authority
3. user-facing wording can be natural, but the decision state stays deterministic

### 7.5 `1.2E` Optional Draft Extension Checkpoint

This slice should open only if real user need appears after `1.2A-D` are green.

Purpose:

1. decide whether draft orders should become first-class governed status coverage

Why this is optional:

1. draft visibility is valuable
2. but it introduces docstatus-mixing policy
3. it should not delay the first submitted-order checkpoint

If opened, this slice should:

1. define explicit draft authority policy
2. make default listing behavior honest about whether drafts are included
3. avoid silently mixing draft and submitted semantics

### 7.6 `1.2F` Closure And Stop Rule

Phase `1.2` should stop when all are true:

1. submitted sales-order listing is browser-valid
2. status and date-scope behavior are stable
3. sales-order detail parity is browser-valid
4. order-status follow-up is browser-valid
5. no sales-order-specific keyword routing was introduced
6. release-gate coverage is green

After that:

1. stop the chapter
2. do not widen straight into trends or payment-terms logic
3. move to the next approved phase step

## 8. Verification Plan

For every `1.2` slice, use both layers:

1. fast deterministic contract tests
2. live/site verification

Required checks:

1. compiler/semantic contract assertions for:
   - `latest N`
   - status filtering
   - time-scope handling
   - detail routing
   - follow-up anchoring
2. browser/UAT prompts for the exact live asks
3. site release-gate promotion only after browser/UAT proves the seam is stable

## 9. Senior Recommendation

Proceed with `1.2` in this exact order:

1. `1.2A` submitted sales-order listing baseline
2. `1.2B` status normalization and date-scope enrichment
3. `1.2C` sales-order detail parity
4. `1.2D` order-status follow-up from detail
5. `1.2E` draft extension only if justified
6. `1.2F` closure

This is the right enterprise-grade plan because:

1. it reuses what Phase `1.1` already proved
2. it obeys the active development guideline
3. it stays contract-first and metadata-first
4. it keeps the first order chapter narrow enough to close cleanly
