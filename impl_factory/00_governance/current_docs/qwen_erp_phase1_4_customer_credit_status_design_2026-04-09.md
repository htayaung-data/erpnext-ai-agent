# Qwen ERP Phase 1.4 Customer Credit Status Design

Status: 1.4A to 1.4F complete
Date: 2026-04-09
Scope: detailed implementation plan for Phase 1, Mini-phase 1.4

## 1. Executive Decision

Phase 1.4 should start with a governed `customer credit exposure` surface, not a full credit-policy or collections engine.

The first implementation must stay:

1. read-only
2. metadata-firs
3. receivable-authority driven
4. bounded to real ERP customer exposure facts
5. small enough to verify with the existing enterprise gate

This means the first target is:

1. governed customer credit-status listing backed by receivable authority
2. overdue / outstanding / credit-balance normalization
3. governed customer credit detail through the existing customer-entity path
4. bounded credit-status follow-up from grounded customer artifacts

This phase should not start with:

1. hard credit-limit enforcement as the primary runtime path
2. policy recommendations about whether to block or allow sales
3. collection strategy or management advice
4. write actions, approvals, or workflow decisions
5. inferred payment behavior or promises not present in governed ERP evidence

## 2. What Phase 1.1 To Phase 1.3 Proved

Phase `1.1`, `1.2`, and `1.3` now give strong implementation guidance for Phase `1.4`.

What worked and should be reused:

1. start from the narrowest real operational ask
2. reuse existing governed families before inventing new runtime lanes
3. use the strongest live ERP authority already present in the tenan
4. keep follow-up continuity grounded on typed artifacts, not raw message tex
5. add browser/UAT checkpoints before calling a slice complete
6. promote smokes into the release-gate pack only after the authority seam is stable
7. document explicit deferrals early so the phase does not widen by enthusiasm

What must not repeat:

1. turning one user phrase into architecture
2. widening from exposure visibility into downstream business-policy claims too early
3. relying on narrative freedom where the source evidence is narrower
4. mixing a new operational chapter with broad cleanup that does not reduce real risk

## 3. Enterprise Guideline Constraints For 1.4

Phase `1.4` must obey the active enterprise guide:

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

This means `Customer Credit Status` must be built as:

1. governed metadata plus typed contract expansion
2. bounded runtime reuse of existing receivable and customer-detail surfaces
3. explicit deferrals for anything broader than exposure visibility and grounded customer credit follow-up

## 4. Current ERP And Repo Findings

The live ERP and codebase support a narrow but valuable `Customer Credit Status` chapter.

### 4.1 Live ERP receivable surface

The current tenant already has strong receivable authority through `Accounts Receivable Summary`.

The report already exposes the core fields needed for a first credit-status chapter:

1. `party`
2. `outstanding`
3. `total_due`
4. `future_amount`
5. aging buckets:
   - `range0`
   - `range1`
   - `range2`
   - `range3`
   - `range4`
   - `range5`
6. `territory`
7. `customer_group`
8. `currency`

Live ERP evidence on `2026-04-09` shows:

1. meaningful wholesale customer exposure already exists for the current Phase 1 business surface:
   - `Chan Aye Mobile Trading Hub`: `160,000` MMK outstanding
   - `Hledan Mobile Trade Center`: `60,000` MMK outstanding
   - `Lanmadaw Digital Wholesale`: `510,000` MMK outstanding
   - `Pazundaung Mobile Distribution`: `945,000` MMK outstanding
   - `Zegyo Mobile Supply House`: `495,000` MMK outstanding
   - `Thaketa Mobile Exchange`: `-249,000` MMK outstanding
2. broader tenant-wide variation also exists:
   - large overdue balances
   - mixed wholesale and retail customers
   - negative balances / advance-like positions
3. this is a real operational surface, not speculative coverage

### 4.2 Live customer master surface

The `Customer` doctype already exposes supporting account and policy context:

1. `customer_group`
2. `territory`
3. `payment_terms`
4. `credit_limits`
5. `is_frozen`
6. `disabled`
7. contact basics such as `mobile_no` and `email_id`

However, current live tenant evidence now shows:

1. customer master records carry populated `default_price_list` and `payment_terms`
2. live `Customer Credit Limit` rows now exist for the active company
3. configured credit-policy context can now be surfaced as a bounded supporting extension

This does not change the correct first authority seam.

The strongest first authority seam is still receivable exposure, and configured credit-limit comparison should remain a bounded extension on top of that governed base.

### 4.3 Current governed assistant surface

The codebase already contains strong reuse candidates:

1. governed capability `accounts_receivable_read`
2. governed `aging` family support backed by `Accounts Receivable Summary`
3. governed ranking support for receivable exposure questions
4. an existing customer detail path in:
   - [entity_detail.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_detail.py)

What this means:

1. `1.4` should reuse receivable and customer-detail infrastructure firs
2. it should not start by inventing a separate free-form credit engine
3. any new `customer credit` semantics should be thin, governed, and anchored to the same receivable authority

### 4.4 Preflight caution

During external preflight, party-filtered `Accounts Receivable Summary` execution showed connector instability in one path.

That does not block the phase, but it does mean:

1. the first bounded runtime should not depend on speculative external-tool assumptions
2. party-level detail should be verified through governed runtime behavior and live/browser checks before promotion

## 5. Authority Model For Customer Credit Status

The first authoritative customer-credit model must be intentionally narrow.

Primary authority should be:

1. `Accounts Receivable Summary.outstanding`
2. `Accounts Receivable Summary.total_due`
3. `Accounts Receivable Summary.future_amount`
4. `Accounts Receivable Summary.range0`
5. `Accounts Receivable Summary.range1`
6. `Accounts Receivable Summary.range2`
7. `Accounts Receivable Summary.range3`
8. `Accounts Receivable Summary.range4`
9. `Accounts Receivable Summary.range5`

Supporting context may include:

1. `Customer.customer_group`
2. `Customer.territory`
3. `Customer.payment_terms`
4. `Customer.is_frozen`
5. `Customer.disabled`
6. recent sales-invoice profile already available through the customer detail path

Deferred authority for later slices only:

1. configured credit-limit comparison when real tenant limit data is reliable
2. credit utilization ratios against absent or ambiguous credit policies
3. recommendations about whether credit should be granted, blocked, or escalated
4. collection risk scoring or collection workflow advice
5. payment behavior inference beyond governed aging evidence

This means:

1. Phase `1.4` should answer customer credit-status questions from receivable and customer-master authority firs
2. it should not become a hidden credit-policy engine
3. if users ask beyond exposure authority, the system should fail closed or defer to a later bounded slice

## 6. Scope For Phase 1.4

### 6.1 In scope

1. customer credit exposure listing
2. overdue customer listing
3. customer credit-balance / negative-balance visibility
4. ranked customer exposure visibility
5. explicit customer credit detail through the existing customer-entity path
6. grounded follow-up from customer credit detail:
   - current outstanding amoun
   - overdue amount / whether overdue exists
   - strongest aging bucke
   - whether the customer is in a negative-balance position
7. contract tests, browser/UAT, and release-gated smokes

### 6.2 Explicitly deferred

1. credit approval or credit hold decision logic
2. collection strategy recommendations
3. promise-to-pay, reminder, or dispute workflows
4. write actions against customer master or finance workflow
5. payment-terms interpretation beyond explicit governed master fields
6. any credit-limit policy basis other than the approved explicit rule for this slice

## 7. Detailed Mini-Phase Plan

### 7.1 `1.4A` Customer Credit Exposure Baseline

Goal:

1. establish the first governed customer credit-status surface using existing receivable authority

Implementation ownership:

1. metadata:
   - define the first `customer credit` operational surface over governed receivable authority
   - prefer reuse of `accounts_receivable_read` and existing families before introducing duplicate capability structure
   - if a thin `customer_credit_status_read` semantic layer is added, it must point back to the same receivable report authority
2. runtime:
   - reuse governed aging and/or ranking family behavior where appropriate
   - no new free-form lane
   - no ad hoc customer-credit string router
3. docs:
   - record the precise authority seam and deferrals immediately

Recommended first-slice source:

1. source report: `Accounts Receivable Summary`
2. default company scope: governed company contex
3. default report date scope: `as_of_today`
4. default primary metric: `Outstanding`
5. first-class customer columns:
   - `Party`
   - `Outstanding Amount`
   - `Total Amount Due`
   - aging buckets
   - `Territory`
   - `Customer Group`

Why:

1. this is the strongest live authority already proven in the tenan
2. it avoids inventing fake credit-limit certainty where the tenant has no real configured limits
3. it gives immediate business value without opening policy risk too early

Example asks covered:

1. `show me customer credit status`
2. `show me customer credit exposure`

Acceptance for `1.4A`:

1. customer exposure comes from governed receivable authority only
2. negative balances are preserved, not normalized away
3. no credit-limit claims are invented
4. no collection-behavior, chronicity, or credit-policy commentary is invented from aging facts alone
5. non-analysis aging reads may prefer governed rendered response over freer narrative if that is the safer way to stay inside the authority seam
6. overdue-only and negative-balance-only filtered asks remain explicitly deferred to `1.4B`
7. same-session self-contained re-asks such as `show me customer credit exposure` after `show customer credit status as of today` must break out as a fresh governed query, not drift into the reasoning lane
8. browser/UAT confirms the first listing shape before any detail widening

### 7.2 `1.4B` Status Normalization And As-Of-Date Enrichmen

Goal:

1. make natural credit-status wording compile into governed exposure meaning without keyword routing

Implementation ownership:

1. metadata:
   - normalize overdue / outstanding / credit-balance / negative-balance inten
   - define bucket-aware credit-status aliases
   - keep report-date semantics explici
2. runtime:
   - reuse governed aging/ranking contracts
   - propagate canonical metric intent into compiler-governed details for adapter filtering
   - no new text-led rescue path
3. tests:
   - cover scope reset, as-of-date handling, and bounded normalization

Important policy:

1. this slice is about `as-of` exposure, not transaction-date lifecycle
2. date handling should align to report-date semantics, not order-style posting-date logic

Example asks covered:

1. `show overdue customers as of today`
2. `show customers with outstanding balances`
3. `show customers with credit balances`
4. `top customers by receivables`

Acceptance for `1.4B`:

1. natural credit-status asks compile through governed metadata
2. prior context does not bleed into full self-contained re-asks
3. the result shape stays consistent across filtered and ranked views
4. browser/UAT confirms overdue-only and credit-balance-only filters in fresh sessions

### 7.3 `1.4C` Customer Credit Detail Parity

Goal:

1. upgrade the existing customer detail path so it can express customer credit status cleanly

Implementation ownership:

1. metadata/contracts:
   - keep reuse of the existing customer entity-detail seam
   - do not invent a new customer drilldown lane
2. runtime:
   - enrich customer detail with receivable exposure facts and aging posture
   - preserve master facts such as customer group, territory, and account-state flags
3. authority:
   - detail stays on customer master plus receivable summary facts only

Likely detail shape:

1. customer profile
2. outstanding / total due
3. aging bucket breakdown
4. customer group / territory
5. disabled / frozen where relevan
6. recent governed invoice history as supporting context only

Acceptance for `1.4C`:

1. explicit customer drilldown stays on single-customer detail
2. no drift into management recommendation or credit approval advice
3. detail remains block-structured and avoids narrative invention for customer credit posture
4. no fabricated configured-limit narrative appears when limit records are absen

### 7.4 `1.4D` Credit-Status Follow-Up From Detail

Goal:

1. answer the most common credit-status follow-ups from grounded customer detail

Supported follow-up classes should be bounded to:

1. `how much is outstanding?`
2. `is this customer overdue?`
3. `how much is overdue?`
4. `which aging bucket is highest?`
5. `does this customer have a credit balance?`

Fail-closed examples:

1. `should we stop selling to this customer?`
2. `what credit limit did they exceed?` when no configured limit exists
3. `when will they pay?`
4. `what should collections do next?`

Acceptance for `1.4D`:

1. follow-up stays on the existing grounded artifact path
2. answers remain deterministic where business-policy overreach risk is high
3. follow-up answers resolve directly from the grounded customer detail blocks
4. unsupported policy or prediction questions fail closed

### 7.5 `1.4E` Configured Credit-Limit Extension

This slice is now approved and implemented for the current tenant because:

1. real tenant `Customer Credit Limit` records are populated
2. customer master records now expose supporting commercial-policy context:
   - `default_price_list`
   - `payment_terms`
3. the comparison basis is now explicitly governed for this slice:
   - primary rule: `Outstanding Amount > Configured Credit Limit`
   - supporting context only:
     - `payment_terms`
     - `default_price_list`
     - available credi
     - utilization ratio

Implemented surface:

1. customer detail now exposes a bounded `Commercial Policy` block
2. grounded follow-up now supports:
   - configured credit limi
   - whether the customer is within / above limi
   - remaining available credi
   - utilization
   - configured payment terms
   - default price lis
3. all answers remain read-only and evidence-bounded

Still out of scope inside `1.4E`:

1. whether sales should be blocked
2. whether approval is required
3. whether collection or finance should take action
4. policy interpretations based on overdue amount instead of the approved basis

### 7.6 `1.4F` Closure And Stop Rule

Phase `1.4` should be considered complete when:

1. the exposure baseline is browser-valid
2. normalization and as-of-date behavior are browser-valid
3. customer credit detail is browser-valid
4. bounded follow-up is browser-valid
5. configured credit-limit extension is browser-valid on live tenant data
6. release-gated smokes are promoted only after those seams are stable

Stop rule:

1. if customer exposure, detail, and bounded follow-up are trustworthy without policy overreach, close the chapter
2. do not widen into a full credit-control platform by defaul

## 8. Verification Plan

Every implemented `1.4` slice should follow the same verification ladder:

1. deterministic contract tests firs
2. site-backed or live smoke second
3. browser/UAT before promotion
4. release-gate promotion only after the browser seam is stable

Priority verification themes:

1. correct receivable authority selection
2. correct handling of overdue vs outstanding vs negative balance
3. correct configured credit-limit basis:
   - outstanding vs configured limi
4. no scope bleed between self-contained re-asks and prior contex
5. no invented credit-limit or collection-policy claims
6. safe fail-closed behavior for unsupported policy questions

## 9. Senior Recommendation

The right enterprise-grade opening for `1.4` is:

1. start from governed customer exposure using `Accounts Receivable Summary`
2. reuse the existing customer detail seam
3. extend into configured credit-limit visibility only after live tenant data exists and the basis is explicitly approved

This is the strongest path because:

1. it aligns with live tenant truth
2. it reuses existing governed infrastructure
3. it avoids pretending the tenant has broader credit-control policy authority than the current governed data actually supports

So the approved order should be:

1. `1.4A` Customer Credit Exposure Baseline
2. `1.4B` Status Normalization And As-Of-Date Enrichmen
3. `1.4C` Customer Credit Detail Parity
4. `1.4D` Credit-Status Follow-Up From Detail
5. `1.4E` Optional Configured Credit-Limit Extension Checkpoin
6. `1.4F` Closure And Stop Rule

That is the correct Phase `1.4` starting plan.
