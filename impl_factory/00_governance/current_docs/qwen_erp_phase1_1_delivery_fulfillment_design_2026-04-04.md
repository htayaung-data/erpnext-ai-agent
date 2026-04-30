# Qwen ERP Phase 1.1 Delivery / Fulfillment Design

Status: checkpoint-complete design note with `1.1C`, `1.1R`, and `1.1D` validated and closed
Date: 2026-04-04
Scope: concrete implementation design for Phase 1, Mini-phase 1.1

## 1. Executive Decision

Phase 1.1 should start with a governed `Delivery Note` read surface, not a broad fulfillment platform.

The first slice should be:

1. read-only
2. metadata-firs
3. grounded on standard ERPNext delivery documents
4. small enough to verify with the existing enterprise gate

This means the first implementation target is:

1. `Delivery Note` listing and status visibility
2. bounded summary over grounded delivery-document rows
3. governed follow-up over the resulting artifac

This phase should not start with:

1. `Delivery Trip` orchestration
2. route optimization
3. ETA or transport intelligence
4. chart/export work
5. cross-document lifecycle decomposition

## 1A. Current Checkpoin

The first strict Phase 1.1 checkpoint is now validated.

What is proven:

1. governed `Delivery Note List` execution is live
2. the first slice runs through the compiled first-turn path
3. exact bounded numeric scope is preserved for the current checkpoint ask:
   - `show me the last 5 delivery notes`
   - title: `Last 5 Delivery Notes`
   - row count: `5`
4. the strict Delivery Note checkpoint smoke is now part of the release-gate path
5. the full enterprise gate was rerun green after this checkpoint was tightened

What this means:

1. the first Delivery Note listing slice is now a validated governed capability surface
2. Phase 1.1 should continue with another bounded Delivery Note improvemen
3. the next step should stay inside Delivery Note behavior and not widen into trends or `Delivery Trip`

Selected next bounded slice:

1. `Delivery Note` date-scope behavior

Why this is next:

1. live `Delivery Note` data confirms that status variation is real, so status-aware filtering is still valuable later
2. however, status filtering would require a more explicit governed status-filter extraction and normalization surface
3. bounded date-scope behavior is the cleaner next enterprise step because:
   - `Delivery Note List` already has a governed `date_field = posting_date`
   - the direct-query executor already knows how to apply `from_date`, `to_date`, and `report_date`
   - the current remaining gap is the compiler path for direct-query listing reports, not a missing delivery-only capability
4. that makes date-scope the better next mini-slice for generic runtime improvement without widening the semantic surface too early

## 1B. Browser / UAT Checkpoin

The `1.1B` browser checkpoint is now materially validated after backend runtime refresh.

What is proven in the browser:

1. `show me the last 5 delivery notes` returns the governed `Delivery Note List` surface with the expected rows, quantity, amount, and status columns
2. `show me the last 5 delivery notes from last month` stays a governed listing and no longer collapses into an incorrect local ranking transform
3. `show me delivery notes with status Completed` returns the correctly filtered governed delivery-note listing
4. `Show me last 7 sale invoices` still works after the Delivery Note continuation path
5. invoice detail follow-up still works after the Delivery Note steps
6. delivery-confirmation questions from invoice detail still fail closed safely when governed delivery proof is not available from the current artifac

What changed operationally:

1. browser/UAT exposed a divergence that the smoke path had hidden
2. the smoke helpers force compiled rollout to 100 percent, while the browser depends on the live backend runtime state
3. the backend runtime was refreshed so the browser path now reflects the current governed continuation logic

What remains outside this checkpoint:

1. `Top 5 customers by revenue last month` may still clarify with `Which report would you like me to use?`
2. that ranking ambiguity is not a `Delivery / Fulfillment` blocker
3. it should be treated as a separate governed ranking/routing item unless a later regression shows it was specifically damaged by Phase 1.1

Current conclusion:

1. `1.1A` Delivery Note listing is browser-valid
2. `1.1B` date-scope and status enrichment are browser-valid
3. Phase 1.1 should not widen to `1.1C` until this checkpoint is recorded and preserved

## 2. Repo And ERP Findings

The current repo and ERP surface support a narrow first slice:

1. current governed metadata has no fulfillment capability ye
2. the ERP instance has standard `Delivery Note` and `Delivery Trip` doctypes
3. the ERP instance also exposes the standard report `Delivery Note Trends`
4. live data exists for `Delivery Note`
5. no live `Delivery Trip` records were found during prefligh

The most important execution signal is:

1. `Delivery Note` is real and active
2. `Delivery Trip` exists structurally but is not yet live in this deploymen

That means the safest enterprise scope is:

1. `Delivery Note` firs
2. `Delivery Trip` later inside the same phase only if live usage appears

## 3. Design Choice

### 3.1 Options considered

Option A: create a brand-new fulfillment family and artifact type immediately

Why rejected for the first slice:

1. larger runtime surface
2. more Python changes than needed
3. higher risk of inventing a family shape before proving the simpler read path

Option B: reuse the existing `transaction_listing` pattern and generalize it from invoice-only to governed document-listing suppor

Why selected:

1. the direct-query path already exists and is proven by `Sales Invoice List`
2. `Delivery Note` naturally fits document-listing behavior
3. the required Python changes can be generic and reusable instead of delivery-specific
4. this keeps the first slice focused on metadata, contracts, and governed listing semantics

Option C: start with `Delivery Note Trends`

Why deferred:

1. it is a script report with less transparent filter/column behavior
2. it is better as a later enrichment step after the document-listing surface is stable
3. the current first-slice need is visibility, not trends

### 3.2 Selected architecture

Phase 1.1 should extend the existing governed document-listing route.

That means:

1. keep using the current direct-query execution path
2. reuse the current canonical listing artifact path where possible
3. generalize invoice-only logic into metadata-driven document listing
4. avoid creating a one-off delivery-only Python path

## 4. First Slice Scope

### 4.1 In scope

The first runtime slice should support:

1. recent delivery-note listing
2. delivery-note listing filtered by customer
3. delivery-note listing filtered by company
4. delivery-note listing filtered by date or recent period
5. delivery-note listing filtered by delivery status when available
6. summary over the grounded list:
   - document coun
   - total quantity
   - total amoun
7. bounded follow-up:
   - presentation transform
   - column projection
   - sort or limi
   - filter refinemen

### 4.2 Out of scope

The following must stay out of the first slice:

1. delivery-route planning
2. driver optimization
3. ETA prediction
4. `Delivery Trip` reasoning as a first-class path
5. delivery-return analytics as a separate artifact family
6. fulfillment trends
7. chart, graph, or export features
8. decomposition across sales order, delivery note, and invoice in one ask

## 5. Intended Metadata Shape

### 5.1 Capability

Add a new governed capability:

1. `fulfillment_read`

Proposed first-slice scope:

1. report family: `delivery_note_list`
2. report name: `Delivery Note List`
3. ontology concepts:
   - `delivery_note`
   - `delivery`
   - `fulfillment`
   - `shipment`
4. supported intent classes for the first slice:
   - `transaction_listing`

Do not broaden the first slice into trend or ranking intent classes yet.

### 5.2 Report registry

Add a new governed report entry:

1. `Delivery Note List`

Recommended grounding mode:

1. `direct_query`

Recommended direct-query target:

1. doctype: `Delivery Note`

Recommended first-slice fields:

1. `name`
2. `posting_date`
3. `customer`
4. `status`
5. `company`
6. `grand_total`
7. `total_qty`
8. `docstatus`
9. `is_return`

Recommended fixed filters:

1. `docstatus = 1`

Recommended date field:

1. `posting_date`

Recommended default order:

1. `posting_date desc, modified desc`

Recommended default limit:

1. `10`

### 5.3 Semantic-resolution registry

The current `transaction_listing` slot shape is invoice-only.

Phase 1.1 should extend it with:

1. `listing_view = delivery_note`

Supported normalization aliases should stay slot-oriented and not become free-form routing rules.

Recommended normalized aliases:

1. `delivery note`
2. `delivery notes`

This should be implemented as slot normalization only, not as Python keyword routing.

### 5.4 Family registry

Do not create a separate family for the first slice.

Instead:

1. extend the existing canonical listing family so it can cover governed business-document lists
2. allow `Delivery Note List` as an approved source repor
3. derive document label and document-type semantics from metadata

This keeps the architecture generic and avoids delivery-only adapter logic.

## 6. Runtime Design Rules

### 6.1 Allowed Python changes

Python changes are acceptable only when they are generic and reusable.

Examples of acceptable changes:

1. generalize transaction-listing resolver from invoice-only to metadata-driven listing views
2. generalize listing artifact adapter from invoice-only fields to metadata-backed document fields
3. improve generic rendering or validation for document-listing artifacts

Examples of forbidden changes:

1. add delivery-only branches in `service.py`
2. add hardcoded `if message contains delivery` routing
3. create a special-case lane only for fulfillmen
4. add one-off delivery rescue logic outside governed metadata

### 6.2 service.py rule

Do not refactor `service.py` as part of Phase 1.1 unless a true blocker appears.

If `service.py` must change, the change must be:

1. minimal
2. behavior-driven
3. generic
4. directly tied to the governed slice

### 6.3 LLM-runtime rule

Phase 1.1 may proceed with the current external runtime dependency because the preflight classified it as a near-blocker, not a stop-work blocker.

However:

1. do not deepen dependency on undocumented runtime behavior
2. keep new Phase 1.1 behavior governed by local metadata and contracts
3. if delivery semantic routing requires prompt-specific behavior outside governed metadata, stop and reassess

## 7. Testing And Verification Plan

### 7.1 Required tests

Add:

1. semantic resolution coverage for `transaction_listing` with `listing_view = delivery_note`
2. compiler coverage for `fulfillment_read`
3. report-registry coverage for `Delivery Note List`
4. family-adapter coverage for generalized document-listing artifacts
5. rendering coverage for delivery-note listing outpu
6. live smoke for recent delivery-note listing

### 7.2 Verification levels

During design and implementation:

```bash
scripts/qwen_verify_enterprise_matrix.sh semantic
```

At the checkpoint:

```bash
scripts/qwen_verify_enterprise_matrix.sh full
```

### 7.3 Measurement rule

Phase 1.1 must record whether the architecture is staying metadata-first.

Measure:

1. JSON and metadata files changed
2. Python files changed
3. whether each Python change is generic or domain-specific

If domain-specific Python branches appear in core routing:

1. log that as architecture debt immediately
2. do not hide it as a normal feature cos

## 8. Proposed Mini-phase Structure Inside Phase 1.1

### 8.1 Mini-phase 1.1A: Delivery Note Listing

Deliver:

1. `fulfillment_read` capability
2. `Delivery Note List` direct-query report entry
3. `listing_view = delivery_note`
4. generalized transaction-listing support for delivery notes
5. strict live smoke for exact delivery-note listing scope
6. full-gate validation after the first strict checkpoin

This is the mandatory first checkpoint.

### 8.2 Mini-phase 1.1B: Delivery Note Status Enrichmen

Only after 1.1A is green:

1. first improve bounded date-scope behavior for `Delivery Note List`
2. then improve status-oriented summary and filtering
3. add bounded status clarification if needed
4. strengthen follow-up over grounded delivery-note artifacts

### 8.3 Mini-phase 1.1C: Optional Trends / Trip Follow-on

Only if the deployment proves the need:

1. evaluate `Delivery Note Trends`
2. evaluate `Delivery Trip` only if live records exis

Do not force 1.1C into the first green checkpoint.

#### 8.3A Current Discovery Decision

The live deployment currently supports a narrow `1.1C` discovery step, but not a `Delivery Trip` slice.

Current live findings:

1. submitted / live `Delivery Note` rows exist:
   - `22`
2. live `Delivery Trip` rows exist:
   - `0`
3. the standard ERPNext report `Delivery Note Trends` exists as a script repor
4. source inspection and live execution show `Delivery Note Trends` requires all of:
   - `company`
   - `fiscal_year`
   - `period`
   - `based_on`
5. the valid `period` values are:
   - `Monthly`
   - `Quarterly`
   - `Half-Yearly`
   - `Yearly`
6. the valid `based_on` values for the sales-trends surface are:
   - `Item`
   - `Item Group`
   - `Customer`
   - `Customer Group`
   - `Territory`
   - `Project`
7. live execution succeeds with a fully valid filter set, for example:
   - `company = Mingalar Mobile Distribution Co., Ltd.`
   - `fiscal_year = 2025-2026`
   - `period = Monthly`
   - `based_on = Customer`
8. successful execution returns:
   - dimension columns such as `Customer`, `Customer Name`, `Territory`, `Currency`
   - dynamic period columns such as `Mar (Qty)` and `Mar (Amt)`
   - total columns `Total(Qty)` and `Total(Amt)`
   - a bar chart over total delivered amoun
9. the report still has a non-trivial governed-fit problem:
   - it is a script report with dynamic columns
   - it is fiscal-year anchored rather than simple date-range anchored
   - its natural output is a trend artifact, not a transaction listing

Selected next `1.1C` candidate:

1. `Delivery Note Trends` discovery and trust evaluation

Deferred inside `1.1C`:

1. `Delivery Trip`

Why:

1. `Delivery Note Trends` is a real report in this deployment and is the smallest meaningful optional extension after listing/date/status
2. `Delivery Trip` is present structurally but not active in this deploymen
3. forcing `Delivery Trip` now would create architecture churn around a ghost surface

Enterprise rule for `1.1C`:

1. start with a design/discovery step only
2. verify report requirements, output trust, and governed fit before runtime wiring
3. if the report surface is too opaque or too noisy, defer `1.1C` rather than widening behavior prematurely

Current `1.1C` trust decision:

1. do not wire `Delivery Note Trends` into runtime ye
2. first design the missing governed report contract for:
   - required filters
   - expected columns
   - time grain
   - trustable trend metrics
3. if that contract cannot be made explicit cleanly, defer `1.1C` instead of adding a weak script-report path

#### 8.3B Governed Contract Candidate For `Delivery Note Trends`

The current discovery supports a narrow candidate contract, but not runtime wiring yet.

Proposed required filters:

1. `company`
2. `fiscal_year`
3. `period`
4. `based_on`

Proposed optional filters:

1. `group_by`

Proposed first trusted scope if implemented later:

1. `based_on = Customer`
2. `period = Monthly`
3. single-company deployment support only
4. delivery quantity and delivery amount only

Why this is the narrowest viable governed scope:

1. the live dataset already returns meaningful customer-level monthly trend rows
2. customer-level grouping aligns with the current business review style better than item-level trend tables
3. monthly grain is the most understandable first trend grain and matches the existing sales-trends defaul

Why this is still not ready for runtime:

1. fiscal-year anchoring needs explicit compiler and follow-up semantics
2. dynamic periodized columns need a governed trend artifact contract, not reuse of the current transaction-listing artifac
3. chart output exists, but chart trust and rendering ownership are part of a later dedicated chart phase

Current enterprise decision:

1. keep `1.1C` in design/discovery mode only
2. do not add `Delivery Note Trends` metadata/runtime wiring in this slice
3. revisit it only after the governed trend-artifact contract is explicitly designed

#### 8.3C Go / No-Go Checkpoin

Decision:

1. `Delivery Note Trends` is a conditional `go`
2. `Delivery Trip` remains a `defer`

Why `Delivery Note Trends` is a conditional `go`:

1. the repo already has an active governed `trend_analytics` family
2. the runtime already has:
   - a generic trend adapter
   - trend-family validation
   - trend rendering
3. live ERP execution proves the report can return a stable period-series surface with explicit filters
4. this means `1.1C` does not require inventing a new artifact family

Why it is only a conditional `go`:

1. current metadata does not yet admit `Delivery Note Trends` into the governed trend family
2. current `fulfillment_read` capability does not yet support `trend_analysis`
3. current trend semantic-routing rules still point to sales/product surfaces, not fulfillmen
4. chart output exists in ERP, but chart ownership remains outside this slice

Enterprise conclusion:

1. `1.1C` may proceed only as a metadata-first onboarding of `Delivery Note Trends` into the existing governed `trend_analytics` family
2. no new artifact family should be created
3. no chart/export behavior should be added in this slice
4. no `Delivery Trip` path should be added in this slice

#### 8.3D Approved Narrow Implementation Shape

If `1.1C` implementation begins, the first trusted scope must stay narrow:

1. report: `Delivery Note Trends`
2. family: `trend_analytics`
3. capability: `fulfillment_read`
4. intent class: `trend_analysis`
5. required filters:
   - `company`
   - `fiscal_year`
   - `period`
   - `based_on`
6. approved first defaults:
   - `period = Monthly`
   - `based_on = Customer`
7. approved first trusted metrics:
   - delivered amoun
   - delivered quantity
8. approved first output:
   - normalized period series
   - governed summary
   - no chart ownership in this slice

Stop rule before implementation:

1. if this cannot be added by extending the existing trend family and metadata contracts, defer `1.1C`
2. do not create delivery-specific runtime branching just to force the report through

Current checkpoint after metadata-first onboarding:

1. `Delivery Note Trends` is now admitted into the governed metadata contracts for:
   - `trend_analytics`
   - `fulfillment_read`
   - explicit report contract defaults and required filters
2. runtime trend admission is now implemented through the existing governed `trend_analytics` family without delivery-specific runtime branching
3. the existing governed `last_year` time-scope contract is now propagated end to end through:
   - metadata ontology and semantic alias maps
   - compiler fiscal-year default resolution
   - trend-family validation
4. the external Qwen runtime image had to be rebuilt, not merely restarted, because the runtime container does not mount repo source code changes directly
5. the current `1.1C` checkpoint is now validated for:
   - `show monthly delivery note trend by customer this fiscal year`
   - `show monthly delivery note trend by customer last year`
   - invoice-detail to delivery-trend breakout continuity
6. the current `1.1C` release-gate path is green after promoting both trend smokes into the release-gate module

#### 8.4 Correction Track Design

Phase `1.1` is not closure-ready yet.

Why:

1. browser/UAT revealed that Delivery onboarding did not fully inherit the older listing contrac
2. the trend surface is not the unreliable seam
3. the unreliable seams are shared listing and continuation behavior

Confirmed drift findings:

1. `give me latest 5 delivery note` is wrongly compiled as a same-day query
   - current interpreted scope becomes `as_of_today`
   - current compiled filters become `2026-04-07 .. 2026-04-07`
   - this violates the older document-listing contract where `latest N` is structural limit, not date scope
2. `give me delivery notes from last month` is correct as a fresh query
   - direct compiler and live single-turn execution return the full March window
   - live result is `8` submitted delivery notes, which matches ERP truth
3. the wrong `5-row` month result happens only after the prior bad `latest 5` turn
   - the second turn is semantically understood as a time-scope refinemen
   - but the continuation path preserves the earlier limit of `5`
   - that means the second defect is continuation-contract drift, not fresh-query time-scope drif
4. `Top 5 customers by revenue last month` is real but separate
   - direct compiler selection is correc
   - live `handle_qwen_user_message` still clarifies
   - this should not be bundled into the Delivery fix

Enterprise classification:

1. shared fresh-query reconciliation bug
2. shared continuation-contract bug
3. separate live-path ranking issue

Approved correction design:

1. fix `latest N` inheritance only in the shared fresh-query reconciliation layer
   - extend the structural limit vs time-scope reconciliation so synthetic `as_of_today` is cleared when the user asked for `latest N` documents rather than `today`
   - do not add Delivery-specific phrase routing
2. fix transaction-listing continuation behavior only in the shared continuation layer
   - transaction listings must not preserve ranking-style limit membership/order during time-scope restatemen
   - time-scope refinement from a prior listing may preserve company and projection shape
   - it must not implicitly preserve the prior numeric limit unless the new request explicitly asks for one
3. keep ranking clarification out of this slice
   - record it and investigate separately after Delivery contract inheritance is restored
4. remove earlier drift rather than layering over i
   - do not add new metadata hacks for Delivery wording
   - do not patch one user phrase
   - do not solve this in rendering tex

Files that should own the correction:

1. [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
   - shared structural limit vs synthetic time-scope reconciliation
2. [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)
   - continuation contract preservation rules
3. [continuation_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/continuation_support.py)
   - authoritative continuation behavior for transaction listings

Files that should not own the correction:

1. report metadata for `Delivery Note List`
2. Delivery-specific runtime branches
3. renderer-only wording patches

Required validation after implementation:

1. compiler probes:
   - `give me latest 5 delivery note`
   - `show me latest 7 sale invoices`
2. live Delivery sequence:
   - `give me latest 5 delivery note`
   - `give me delivery notes from last month`
   - expected second turn: full March result, not preserved `5`
3. browser/UAT:
   - the same two prompts
   - plus canonical Delivery prompts already used in checkpoints
4. separate live ranking check:
   - `Top 5 customers by revenue last month`
   - validate separately, do not treat it as acceptance criteria for the Delivery correction

Current correction-track closure:

1. `give me latest 5 delivery note` is now browser-valid again as latest documents, not a same-day empty window
2. `give me delivery notes from last month` is now browser-valid again as the full March submitted set:
   - `8` documents
   - `41` quantity
   - `2,446,000` amoun
3. governed `Delivery Note` detail drilldown now works from the listing surface:
   - `tell me more about MAT-DN-2026-00016`
4. the new `Delivery Note` detail continuity smoke is now in the release-gate path
5. the release-gate module is green with the correction included
6. `1.1R` should now be treated as closed

## 9. Next Bounded Slice: 1.1D Invoice-to-Delivery Proof

The next bounded Phase `1.1` slice should be:

1. `1.1D` Invoice-to-Delivery Proof

Why this stays in Phase 1:

1. the question is a common operational ask:
   - `items from this invoice are already delivered?`
2. it requires governed evidence from more than one artifac
3. but it is still a narrow operational proof ask, not a broad multi-artifact analysis engine

What `1.1D` should do:

1. start from an already grounded invoice-detail artifac
2. follow only governed operational evidence:
   - linked `Delivery Note`
   - linked `Sales Order`
   - or other direct ERP delivery proof if that link is authoritative
3. answer one bounded proof question:
   - fully delivered
   - partially delivered
   - not yet delivered
   - or insufficient governed evidence

What `1.1D` should not do:

1. do not become a general composite reconciliation engine
2. do not widen into payment + stock + delivery + returns in one narrative
3. do not guess delivery state from invoice status alone
4. do not defer the narrow proof question all the way to Phase 3

Enterprise implementation rule for `1.1D`:

1. reuse the current invoice-detail and delivery-note-detail ecosystem
2. add only the minimum governed evidence chain needed for delivery proof
3. if the evidence chain is not explicit enough, fail closed with a governed limitation instead of inference

Current `1.1D-0` foundation findings:

1. the ERP and codebase already expose the correct linkage surface
   - `Sales Invoice Item` has:
     - `delivery_note`
     - `dn_detail`
     - `sales_order`
     - `so_detail`
   - ERPNext dashboard wiring already treats `Delivery Note` as an internal/external linked reference from `Sales Invoice`
2. the current deployment has three real invoice-level buckets only:
   - `invoice_updates_stock`
   - `all_items_linked_delivery_note`
   - `insufficient_evidence`
3. live invoice census for `Mingalar Mobile Distribution Co., Ltd.` found:
   - `164` submitted invoices where `update_stock = 1`
   - `7` submitted invoices where all items are linked to `Delivery Note` / `dn_detail`
   - `8` submitted invoices with neither direct delivery-note links nor stock-updating invoice delivery proof
   - `0` live invoices in a `sales_order only` fallback bucke
   - `0` live invoices with mixed direct-proof and no-proof item rows
4. `Sales Invoice Item.delivered_qty` is not authoritative for this slice
   - live linked invoices still show `delivered_qty = 0`
   - proof should not be built from that field
5. `Sales Order.per_delivered` and `Sales Order Item.delivered_qty` are useful supporting context but should not be the first proof source for this deploymen
   - they describe order-level delivery progress
   - they do not provide a cleaner invoice-level proof surface than the direct invoice-item links already do
6. return nuance is real in the live data
   - return invoices exist in both direct-proof buckets:
     - `delivery_note`-linked return invoices
     - `update_stock = 1` return invoices
   - first implementation must not answer a return invoice as if it were a standard outbound delivery without saying it is a return / reversal contex

`1.1D` first trusted scope should therefore be narrower than originally feared:

1. if submitted `Sales Invoice.update_stock = 1`, treat the invoice itself as direct governed delivery proof
2. else if every invoice item has a submitted `delivery_note` + `dn_detail`, treat that as direct governed delivery proof
3. else fail closed as insufficient governed delivery evidence

Deferred from the first `1.1D` implementation slice:

1. sales-order-only fallback proof
2. mixed invoice-item proof states inside one invoice
3. broad reconciliation across invoice, delivery, stock, and paymen

Current `1.1D-1` implementation note:

1. the first implementation now reuses the existing `entity_detail` plus artifact-boundary ecosystem instead of adding a new invoice-to-delivery lane
2. `Sales Invoice` detail artifacts now carry a governed `delivery_proof` section with only two accepted direct-proof states:
   - `direct_delivery_proven_via_invoice_stock`
   - `direct_delivery_proven_via_linked_delivery_note`
3. explicit return variants are also captured:
   - `direct_return_proven_via_invoice_stock`
   - `direct_return_proven_via_linked_delivery_note`
4. if the invoice does not meet one of those direct-proof states, the system still fails closed as `insufficient_governed_delivery_evidence`
5. targeted live verification is green for both sides:
   - positive proof answer for `ACC-SINV-2026-00194`
   - fail-closed boundary answer for unsupported invoice `ACC-SINV-2026-00192`
6. the direct-proof follow-up now also supports the next bounded date question:
   - `when it was delivered?`
   - answer comes from the same governed proof payload, using linked submitted `Delivery Note` posting date(s)
7. release-gate promotion is intentionally deferred to the next slice after browser/UAT revalidation

Current `1.1D-2` closure note:

1. browser/UAT is now green for supported invoice proof in both continued-chat and fresh-chat flows:
   - `tell me more about ACC-SINV-2026-00194`
   - `that item already delivered to the customer?`
   - `when it was delivered?`
2. fresh-chat explicit invoice identifiers now route through the shared governed `entity_detail` path before compiled-first-turn handling
3. the fresh-chat parity fix was implemented at shared orchestration level, not as an invoice-specific keyword or single-case patch
4. the direct proof answer remains bounded to explicit governed evidence:
   - submitted stock-updating invoice proof
   - or submitted linked `Delivery Note` proof
5. unsupported invoices still fail closed when that evidence is insufficien
6. both the standard invoice-delivery proof smoke and the fresh-chat parity smoke are now release-gated
7. `1.1D` should now be treated as closed

Phase `1.1` closure note:

1. `Delivery Note` listing, date-scope, status, trend, and detail continuity are browser-valid and release-gated
2. invoice-to-delivery proof is now browser-valid and release-gated at its narrow trusted scope
3. the current remaining ranking ambiguity around `Top 5 customers by revenue last month` is not a Phase `1.1` blocker
4. Phase `1.1` should now be treated as checkpoint-complete
5. the next bounded operational expansion should move to `1.2` Sales Order Status

## 10. Stop Rules For Phase 1.1

Stop and checkpoint when all are true:

1. recent delivery-note questions route through governed metadata
2. runtime behavior remains contract-first and fail-closed
3. no new delivery-specific keyword routing is introduced
4. the listing artifact is generic enough to support more than invoices
5. exact numeric scope is preserved for the bounded first checkpoin
6. the full enterprise gate is green

Do not keep expanding Phase 1.1 into trends, trips, or export work after the first green checkpoint.

## 11. Senior Recommendation

Proceed with Phase 1.1 through `Delivery Note` first.

This is the best enterprise-grade first slice because:

1. it is real in this deploymen
2. it reuses a proven governed direct-query path
3. it expands operational coverage without introducing a new architecture pattern
4. it gives a measurable test of whether the current metadata-first architecture scales to a new business domain
