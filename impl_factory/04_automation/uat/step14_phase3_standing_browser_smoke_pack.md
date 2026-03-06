# Phase 3 Standing Browser Smoke Pack

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: required browser/manual parity pack for shared-runtime changes  
Status: active Phase 3 standing smoke pack

## Purpose
This pack is the minimum browser/manual confirmation set that must remain healthy after significant shared-runtime changes.

It exists because replay-green alone is not enough for this product. Real browser sessions have repeatedly exposed:

1. topic carryover defects
2. latest-result authority defects
3. projection/transform drift
4. browser/runtime parity gaps

This pack is intentionally small. It is not a full UAT matrix. It is the standing browser parity control for Phase 3 and later phases.

## Execution Rules
1. Use the browser UI, not replay scripts.
2. Start a fresh chat for each numbered pack unless the case explicitly says to continue in the same session.
3. Record:
   - prompt(s)
   - visible report title
   - pass/fail
   - screenshot if failed
4. A case fails if any of these happen:
   - wrong report
   - wrong grain
   - stale topic carryover
   - wrong transform/projection behavior
   - retry needed to succeed
   - internal/debug leakage

## Pack A: Customer Ranking + Scale
Risk tier: Tier 1  
Protects:

1. finance/sales ranking correctness
2. transform-followup reuse of active result
3. repeat-scale idempotence

Steps:

1. `Top 10 customers by revenue last month`
2. `Show as Million`
3. `Show as Million`

Expected:

1. `Customer Ledger Summary`
2. same ranked customer set
3. revenue scaled to millions
4. second scale request does not drift or collapse

## Pack B: Product Ranking + Projection
Risk tier: Tier 2  
Protects:

1. product ranking
2. add-column follow-up
3. restrictive projection semantics

Steps:

1. `Top 10 products by sold quantity last month`
2. `with Item Name`
3. `Give me Item Name and Sold Qty only`
4. `Give me Item Name Only`

Expected:

1. first turn returns item + sold quantity
2. second turn adds `Item Name`
3. third turn keeps only `Item Name` and `Sold Quantity`
4. fourth turn keeps only `Item Name`

## Pack C: Supplier Ranking + Scale
Risk tier: Tier 1  
Protects:

1. supplier finance/purchasing parity
2. ranking follow-up reuse
3. scale transform on non-customer party ranking

Steps:

1. `Top 10 suppliers by purchase amount last month`
2. `Show in Million`

Expected:

1. `Supplier Ledger Summary`
2. purchase amount remains the metric
3. same supplier set
4. values scaled to millions

## Pack D: Warehouse Ranking Correction + Scale
Risk tier: Tier 1  
Protects:

1. correction/rebind state authority
2. ranking direction carryover
3. aggregate-row-safe ranking
4. scale transform after correction

Steps:

1. `Lowest 3 warehouses by stock balance`
2. `I mean Top`
3. `Show as Million`

Expected:

1. first turn shows bottom 3 warehouses
2. second turn switches to top warehouses without drifting to another report
3. third turn keeps the same 3 warehouse rows and scales values

## Pack E: Latest-Record Clarification
Risk tier: Tier 1  
Protects:

1. latest-record doctype clarification
2. resume pinning
3. doctype disambiguation

Steps:

1. `Show me the latest 7 Invoice`
2. `Sales Invoice`

Expected:

1. first turn asks which record type
2. second turn returns latest 7 Sales Invoices
3. no extra clarification loop

## Pack F: Finance Parity
Risk tier: Tier 1  
Protects:

1. receivable/payable party ledger disambiguation
2. first-turn finance read correctness

Steps:

1. `Show accounts receivable as of today`
2. `Show me the latest Purchase 7 Invoice`

Expected:

1. receivables path returns `Customer Ledger Summary`
2. latest purchase invoice path returns `Latest Purchase Invoice`

## Pack G: Write Cancel Safety
Risk tier: Tier 1  
Protects:

1. browser-visible write safety
2. confirm/cancel control

Steps:

1. `Delete ToDo TEST-123`
2. `cancel`

Expected:

1. first turn asks for explicit confirmation
2. second turn cancels without execution

## When This Pack Must Be Rerun
Rerun this full standing smoke pack when:

1. `read_engine.py` orchestration changes
2. `memory.py` changes
3. `resume_policy.py` changes
4. `transform_last.py` changes
5. `response_shaper.py` changes
6. `semantic_resolver.py` or capability-metadata changes affect core read behavior
7. release-candidate or phase-close evidence is being prepared

## Minimum Pass Rule
This standing pack is considered green only when:

1. every pack above passes
2. no prompt must be repeated to succeed
3. no stale topic/report carryover occurs
4. no wrong-report drift occurs

## Operational Use
This pack is:

1. smaller than the full UAT matrix
2. mandatory for shared-runtime confidence
3. the browser/manual counterpart to the core replay pack
