# Qwen ERP Phase 1.5 Operational Phase Closure

Status: closure complete  
Date: 2026-04-09  
Scope: closure verification for Phase 1 operational mini-phases `1.1` through `1.4`

## 1. Executive Judgment

Phase `1.5` has now completed the right closure check.

The result is:

1. Wave 1 operational slices are materially active and release-gated through the post-contract site suite
2. the new `1.4` customer-credit seams are now represented in the release-gate pack
3. one shared transaction-listing validator drift was found and fixed during closure
4. one older `H5` reasoning-lane blocker was repaired during closure by suppressing contradictory presentation-only follow-up payloads when grounded reasoning was already the accepted lane
5. the direct guarded recommendation smoke and the instrumented `H5` sanity components now run green end to end

That means Phase `1.5` is now honestly closure-complete for Wave 1.

## 2. What Was Added In This Closure Slice

### 2.1 `1.4` release-gate promotion

The site-backed post-contract release-gate module now includes the Phase `1.4` operational seams:

1. `run_phase1_4_customer_credit_exposure_smoke`
2. `run_phase1_4_customer_credit_overdue_smoke`
3. `run_phase1_4_customer_credit_balance_smoke`
4. `run_phase1_4_customer_credit_scope_reset_smoke`
5. `run_phase1_4_customer_credit_detail_followup_smoke`

This closes the previous gap where `1.4` was browser-valid and locally tested, but not yet promoted into the active site gate pack.

### 2.2 Shared validator repair found during closure

Closure verification exposed a real shared-runtime drift:

1. `transaction_listing` validation was canonically treating `Outstanding Amount` as `outstanding_total`
2. document-list families still emit `outstanding_amount`
3. this caused the old `Phase 1.1` session-reset smoke to fail during the gate run

The fix was bounded and family-specific:

1. `transaction_listing` validation now accepts canonical outstanding requests as `outstanding_amount`
2. this keeps aging-family normalization intact while preserving document-list semantics

### 2.3 Reasoning-lane suppression repair found during closure

Closure verification also exposed a real orchestration drift in the old `H5` recommendation guardrail path:

1. a grounded reasoning follow-up such as `explain this accounts receivable summary` could still be misread by the semantic follow-up interpreter as a presentation-only request with contradictory query-shape fields
2. the governed follow-up boundary would then correctly force a fresh query breakout
3. this prevented the reasoning lane from owning a turn that had already been semantically accepted as grounded ERP reasoning

The fix was bounded and architecture-aligned:

1. contradictory presentation-only follow-up payloads are now suppressed when grounded reasoning has already been accepted
2. this fix lives in shared scope orchestration rather than a single-case smoke hack
3. targeted regression coverage was added so valid structured refinements still remain untouched

## 3. Verification Results

### 3.1 Verified green in this slice

Verified during this closure pass:

1. local unit check:
   - `TestSemanticFinancialResolution.test_transaction_listing_family_validation_accepts_outstanding_total_canonical_request`
   - `TestSemanticFinancialResolution.test_reasoning_supersedes_contradictory_presentation_only_followup`
   - `TestSemanticFinancialResolution.test_reasoning_does_not_supersede_legitimate_structured_followup`
2. direct site smoke rerun:
   - `run_phase1_1_delivery_note_session_reset_smoke`
   - `run_h4_recommendation_guarantee_stays_bounded_smoke`
3. direct live reasoning verification:
   - the two-turn `Accounts Receivable Summary` reasoning path now returns `erp_business_reasoning` for `explain this accounts receivable summary`
4. instrumented `H5` sanity-pack verification:
   - `frontdoor_boundary`
   - `reasoning_live_rollout`
   - `boundary_responses`
   - `recovery_execution`
   - `adversarial_recommendation_guardrail`
   - all completed green in one site-backed step-by-step rerun
5. site release-gate module observations:
   - all promoted Phase `1.4` smokes ran green
   - the new `1.4` customer detail + follow-up smoke ran green

## 4. Closure Decision

Current decision:

1. Phase `1.5` is now closure-complete for Wave 1
2. the previous `H5` reasoning-lane blocker is repaired
3. Phase `2` work can proceed without carrying forward a known operational closure defect

## 5. Stop Rule

Do not reopen Phase `1.5` unless:

1. a later shared-lane change reintroduces a release-gate regression
2. a future phase alters the post-contract gate pack enough to require fresh closure verification
