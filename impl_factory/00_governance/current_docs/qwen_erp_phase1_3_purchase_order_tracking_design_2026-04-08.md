# Qwen ERP Phase 1.3 Purchase Order Tracking Design

Status: active implementation design note
Date: 2026-04-08
Scope: detailed implementation plan for Phase 1, Mini-phase 1.3

## 1. Executive Decision

Phase 1.3 should start with a governed `Purchase Order` tracking surface, not a broad procurement lifecycle engine.

The first implementation must stay:

1. read-only
2. metadata-firs
3. procurement-status-authority driven
4. bounded to real ERP purchase-order facts
5. small enough to verify with the existing enterprise gate

This means the first target is:

1. governed `Purchase Order` listing
2. status-aware filtering and date-scope handling
3. governed `Purchase Order` detail
4. bounded order-status follow-up from grounded purchase-order artifacts

This phase should not start with:

1. cross-document reconciliation across purchase order, purchase receipt, and purchase invoice
2. supplier aging or payable reasoning as a primary path
3. trend/reporting expansion as the entry slice
4. workflow-write or approval actions
5. actual receipt-event proof by inference from downstream documents unless a later bounded slice explicitly approves that widening

## 2. What Phase 1.1 And Phase 1.2 Proved

Phase `1.1` and Phase `1.2` now give strong implementation guidance for Phase `1.3`.

What worked and should be reused:

1. start from the narrowest real operational ask
2. reuse the existing `transaction_listing` family before inventing a new family
3. introduce a direct-query document-listing report before trends or analytics
4. reuse `entity_detail` instead of inventing a new drilldown lane
5. keep follow-up continuity grounded on typed artifacts, not raw message tex
6. add browser/UAT checkpoints before calling a slice complete
7. promote smokes into the release-gate pack only after the authority seam is stable

What must not repeat:

1. letting a new domain diverge from existing shared listing semantics
2. mixing expansion with broad cleanup before the bounded checkpoint is closed
3. patching phrase-level behavior before checking whether governed metadata already owns the rule
4. widening from status visibility into downstream proof too early

## 3. Enterprise Guideline Constraints For 1.3

Phase `1.3` must obey the active enterprise guide:

1. contract firs
2. metadata owns business policy
3. compiler enforces deterministically
4. fail closed when evidence is insufficien
5. no keyword routing
6. no single-case prompt fixes
7. two-layer verification is required:
   - fast deterministic contract tests
   - live/site verification where state matters
8. expand only after the previous chapter is closed
9. stop when the stop rule is me

This means `Purchase Order Tracking` must be built as:

1. governed metadata plus typed contract expansion
2. bounded runtime reuse
3. explicit deferrals for anything broader than purchase-order status visibility and follow-up

## 4. Current ERP And Repo Findings

The live ERP and codebase support a narrow but valuable `Purchase Order` tracking chapter.

### 4.1 Live ERP surface

The `Purchase Order` doctype already exposes the right operational status fields:

1. `status`
2. `docstatus`
3. `transaction_date`
4. `schedule_date`
5. `grand_total`
6. `total_qty`
7. `per_received`
8. `per_billed`
9. `supplier`
10. `company`

The live `Purchase Order Item` rows also already expose the right bounded detail fields:

1. `qty`
2. `received_qty`
3. `billed_amt`
4. `schedule_date`
5. `item_code`
6. `item_name`

Direct live ERP evidence on `2026-04-08` shows:

1. total `Purchase Order` count is `8`
2. all current live records are submitted (`docstatus = 1`)
3. the current meaningful live statuses are:
   - `To Bill`
   - `To Receive and Bill`
4. live order-level variation already exists in:
   - `per_received`
   - `per_billed`
   - `schedule_date`

This is a real operational surface, not speculative coverage.

### 4.2 Standard ERP report surface

ERP already exposes standard buying reports relevant to later expansion:

1. `Purchase Order Analysis`
2. `Purchase Order Trends`
3. `Purchase Analytics`
4. `Procurement Tracker`
5. `Item-wise Purchase History`

These are important, but they should not be Phase `1.3` entry points.

### 4.3 Current assistant surface

The governed metadata currently has no mature `Purchase Order` capability surface.

What already exists and should be reused:

1. generic direct-query listing infrastructure
2. shared `transaction_listing` family
3. shared `entity_detail` family
4. shared continuation and follow-up contracts
5. shared browser/UAT and release-gate pattern proven in Phase `1.1` and `1.2`

What does not yet exist:

1. `Purchase Order List` report metadata
2. `Purchase Order` semantic-resolution entries
3. `Purchase Order` status normalization policy
4. `Purchase Order` explicit entity-detail suppor
5. `Purchase Order` follow-up aliases for received / billed / planned receipt due date

## 5. Authority Model For Purchase Order Tracking

The first authoritative purchase-order model must be intentionally narrow.

Primary authority should be:

1. `Purchase Order.status`
2. `Purchase Order.docstatus`
3. `Purchase Order.per_received`
4. `Purchase Order.per_billed`
5. `Purchase Order.schedule_date`

Supporting context may include:

1. `grand_total`
2. `total_qty`
3. `supplier`
4. `company`
5. item-row `received_qty`
6. item-row `billed_amt`

Deferred authority for later slices only:

1. purchase-receipt-derived actual receipt proof
2. purchase-invoice-derived billing narrative beyond order-level billed percentage
3. procurement-tracker reasoning and lifecycle explanation
4. supplier performance or payable analysis

This means:

1. Phase `1.3` should answer purchase-order tracking questions from purchase-order authority firs
2. it should not become a hidden procurement composite engine
3. if users ask beyond order authority, the system should fail closed or defer to a later bounded slice

## 6. Scope For Phase 1.3

### 6.1 In scope

1. latest purchase-order listing
2. date-scoped purchase-order listing
3. status-filtered purchase-order listing
4. submitted purchase-order visibility
5. explicit purchase-order detail by identifier
6. grounded follow-up from purchase-order detail:
   - current status
   - received percentage
   - billed percentage
   - planned receipt date
7. contract tests, browser/UAT, and release-gated smokes

### 6.2 Explicitly deferred

1. `Purchase Order Trends` as a first-slice entry poin
2. `Purchase Order Analysis` as the first artifact surface
3. `Purchase Analytics`
4. `Procurement Tracker`
5. draft-versus-submitted mixed policy unless a bounded extension is explicitly approved
6. actual-receipt-date answers from downstream purchase-receipt documents
7. purchase-order to bill/invoice composite storytelling

## 7. Detailed Mini-Phase Plan

### 7.1 `1.3A` Submitted Purchase Order Listing Baseline

Goal:

1. establish the first governed `Purchase Order` read surface through the already-proven document-listing pattern

Implementation ownership:

1. metadata:
   - add capability `purchase_order_read`
   - add report `Purchase Order List`
   - map it to `transaction_listing`
2. runtime:
   - reuse direct-query execution
   - no new family
   - no new lane
3. docs:
   - record scope and stop rule immediately

Recommended first-slice report shape:

1. doctype: `Purchase Order`
2. grounding mode: `direct_query`
3. date field: `transaction_date`
4. initial fields:
   - `name`
   - `transaction_date`
   - `supplier`
   - `status`
   - `company`
   - `grand_total`
   - `total_qty`
   - `per_received`
   - `per_billed`
   - `schedule_date`
   - `docstatus`
5. default order:
   - `transaction_date desc, modified desc`

Policy choice for `1.3A`:

1. start with submitted orders only (`docstatus = 1`)
2. treat draft visibility as a later bounded extension

Why:

1. it mirrors the successful Delivery and Sales Order entry strategy
2. it keeps the first authority surface simple
3. it avoids mixing draft workflow policy into the first checkpoin

Example asks covered:

1. `show me latest 5 purchase orders`
2. `show me submitted purchase orders from last month`
3. `show me purchase orders with status To Bill`

Acceptance for `1.3A`:

1. `latest N` means structural limit, not current-day scope
2. status-filtered purchase-order listing works through governed metadata
3. summary totals are grounded from list rows only
4. no purchase-order-specific keyword routing is introduced

Implementation checkpoint for `1.3A`:

1. the governed capability `purchase_order_read` is now registered
2. the governed direct-query report `Purchase Order List` is now active for submitted orders only
3. `transaction_listing` now admits `Purchase Order List` without introducing a new lane
4. governed metadata now owns:
   - listing-view slot support for `purchase_order`
   - the direct-query report surface
   - report-surface evidence posture for the governed direct-query surface
5. deterministic validation is green:
   - [test_purchase_order_listing_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_purchase_order_listing_contracts.py)
   - [test_semantic_financial_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_semantic_financial_resolution.py)
6. bounded live/site validation is green via `run_phase1_3_purchase_order_listing_smoke`
7. browser/UAT exposed two real residuals:
   - zero-row summaries were rendering `Document Count` as blank instead of `0`
   - a full re-ask like `show me purchase orders with status To Bill` could still inherit the prior month scope implicitly
8. both residuals were corrected in shared layers, not with Purchase-Order-only routing:
   - zero-value summary rendering is now preserved generically
   - self-contained governed re-asks now break out of prior date context before continuation backfill can leak the previous month
9. `1.3A` is now closure-ready, and the next active implementation move is `1.3B`

### 7.2 `1.3B` Status Normalization And Date-Scope Enrichmen

Goal:

1. make natural purchase-order status phrasing compile into the governed status surface without introducing raw-text routing

What this slice should add:

1. governed status aliases for:
   - `To Bill`
   - `To Receive and Bill`
2. natural phrasing support like:
   - `purchase orders to bill`
   - `purchase orders to receive`
   - `completed purchase orders`
3. stable composition with time-scope phrases like:
   - `last month`
   - `latest`

Important rule:

1. status normalization must come from governed filter-value metadata, not prompt-specific if/else code

Acceptance for `1.3B`:

1. status aliases resolve through metadata only
2. date-scope and status can be combined without losing either
3. the shared transaction-listing contract stays intac

Implementation checkpoint for `1.3B`:

1. governed `Purchase Order List` metadata now owns status aliases for:
   - `To Receive`
   - `To Bill`
   - `To Receive and Bill`
   - `Completed`
   - `Closed`
2. the shared fresh-query scalar-filter bridge now applies governed filter-value aliases even when the message does not first resolve a canonical dimension key
3. the exact two-turn regression path is now green in live/site validation via:
   - `run_phase1_3_purchase_order_status_scope_reset_smoke`
4. shared transaction-listing projection now preserves family identity columns for filtered purchase-order listings:
   - `Supplier` remains visible as the party column
   - `Status` remains visible when the request explicitly filters by status
5. deterministic validation remains green:
   - [test_purchase_order_listing_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_purchase_order_listing_contracts.py)
   - [test_semantic_financial_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_semantic_financial_resolution.py)
6. browser/UAT is now the next required gate before `1.3B` can be treated as closure-ready

### 7.3 `1.3C` Purchase Order Detail Drilldown Parity

Goal:

1. make explicit `PUR-ORD-...` identifiers route through the existing governed `entity_detail` path

Required detail authority:

1. `status`
2. `supplier`
3. `transaction_date`
4. `schedule_date`
5. `per_received`
6. `per_billed`
7. `grand_total`
8. `total_qty`
9. item rows including:
   - `qty`
   - `received_qty`
   - `billed_amt`

Important rule:

1. detail must stay on purchase-order authority only
2. do not inject purchase-receipt proof into the detail artifac

Acceptance for `1.3C`:

1. fresh-chat explicit identifier goes straight to purchase-order detail
2. no drift into list/report summary
3. no hidden downstream receipt-proof language

Implementation checkpoint for `1.3C`:

1. explicit `PUR-ORD-...` identifiers now resolve through the shared governed `entity_detail` path
2. governed `Purchase Order` detail now stays on purchase-order authority only:
   - `status`
   - `supplier`
   - `transaction_date`
   - `schedule_date`
   - `per_received`
   - `per_billed`
   - `grand_total`
   - `total_qty`
   - item-row `qty`, `received_qty`, and `billed_amt`
3. receipt status and billing status are now derived deterministically from order-level percentages, not from downstream purchase-receipt or purchase-invoice evidence
4. Purchase Order detail now uses governed local narration for this slice instead of free artifact narrative generation, because repeated AI narration attempts leaked unsupported receipt-event and payable-style claims
5. deterministic validation is green:
   - [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
   - [test_purchase_order_listing_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_purchase_order_listing_contracts.py)
6. bounded live/site validation is green via:
   - `run_phase1_3_purchase_order_detail_smoke`
7. browser/UAT is now green for `1.3C`:
   - explicit `PUR-ORD-...` drilldowns stay on single-document purchase-order detail
   - detail remains bounded to purchase-order authority only
   - unsupported receipt-event and payable-style narrative claims are no longer presen

### 7.4 `1.3D` Order-Status Follow-Up From Detail

Goal:

1. support the next bounded procurement follow-ups from grounded purchase-order detail

Follow-ups in scope:

1. `is it received?`
2. `how much is received?`
3. `is it billed?`
4. `how much is billed?`
5. `when is receipt due?`

Authority for this slice:

1. `per_received`
2. `per_billed`
3. `schedule_date`
4. item-row `received_qty`
5. item-row `billed_amt`

Explicitly blocked in this slice:

1. `when was it received?`
2. `which purchase receipt received it?`

Why:

1. those require downstream receipt evidence, not purchase-order authority

Acceptance for `1.3D`:

1. the follow-up remains anchored to the current purchase-order detail artifac
2. no raw text heuristics become hidden authority
3. actual receipt-event date still fails closed without downstream receipt evidence

Implementation checkpoint for `1.3D`:

1. governed semantic aliases now cover the bounded purchase-order follow-up classes:
   - `receipt_progress_percent`
   - `billing_progress_percent`
   - `planned_receipt_date`
2. the shared grounded artifact evidence path now supports purchase-order follow-ups from purchase-order authority only:
   - `per_received`
   - `per_billed`
   - `schedule_date`
   - item-row `received_qty`
   - item-row `billed_amt`
3. supported follow-ups now answer from the current purchase order detail artifact:
   - `is it received?`
   - `how much is received?`
   - `is it billed?`
   - `how much is billed?`
   - `when is receipt due?`
4. unsupported widening now fails closed:
   - `when was it received?` requires downstream purchase-receipt evidence and now stops at the governed boundary
5. purchase-order follow-up answers now stay deterministic end-to-end in this slice, so the runtime does not re-narrate them with free AI wording
6. deterministic validation is green:
   - [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
   - [test_purchase_order_listing_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_purchase_order_listing_contracts.py)
7. bounded live/site validation is green via:
   - `run_phase1_3_purchase_order_status_followup_smoke`
   - site `test_entity_detail_contracts`
8. browser/UAT is now green for `1.3D`:
   - receipt-progress follow-up stays anchored to the current purchase-order detail artifac
   - billed-progress and planned-receipt-date follow-ups answer from purchase-order authority only
   - actual receipt-event date still stops safely at the governed boundary
9. `1.3C` and `1.3D` are now promoted into the site release-gate module:
   - [test_post_contract_release_gates.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_post_contract_release_gates.py)
10. the site-backed release-gate module is green after that promotion

### 7.5 `1.3E` Optional Draft / Receipt Extension Checkpoin

This slice should open only if real user need appears after `1.3A-D` are green.

Possible future scope:

1. draft purchase-order coverage
2. explicit docstatus-mixing policy
3. bounded receipt-proof widening from purchase-order detail

Why this is optional:

1. it adds policy complexity
2. it should not delay the first submitted-order checkpoin

### 7.6 `1.3F` Closure And Stop Rule

Phase `1.3` should stop when all are true:

1. submitted purchase-order listing is browser-valid
2. status and date-scope behavior are stable
3. purchase-order detail parity is browser-valid
4. purchase-order status follow-up is browser-valid
5. no purchase-order-specific keyword routing was introduced
6. release-gate coverage is green

After that:

1. stop the chapter
2. do not widen straight into procurement analytics or payable reasoning
3. move to the next approved phase step

## 8. Verification Plan

For every `1.3` slice, use both layers:

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

Proceed with `1.3` in this exact order:

1. `1.3A` submitted purchase-order listing baseline
2. `1.3B` status normalization and date-scope enrichmen
3. `1.3C` purchase-order detail parity
4. `1.3D` order-status follow-up from detail
5. `1.3E` draft / receipt extension only if justified
6. `1.3F` closure

This is the right enterprise-grade plan because:

1. it reuses what Phase `1.1` and Phase `1.2` already proved
2. it obeys the active development guideline
3. it stays contract-first and metadata-firs
4. it keeps the first procurement chapter narrow enough to close cleanly
