# Phase 4 Standing Browser Smoke Refresh Pack

Date: 2026-03-18  
Owner: AI Runtime Engineering  
Scope: first Phase 4 full standing browser smoke refresh  
Status: execution pack ready

## 1. Purpose

This pack refreshes the standing browser/manual truth after Phase 3 closure and Phase 4 starter-pack approval.

The goal is simple:

1. replace carry-forward browser status with fresh evidence
2. confirm no replay/browser contradiction exists on core standing flows
3. allow the weekly operations review to move from `Watch` toward `Stable`

## 2. Execution Rules

1. Use the browser UI only.
2. Use a fresh chat for each numbered pack unless explicitly told to continue in the same session.
3. Do not retry a failed prompt to “make it pass”.
4. For every case, record:
   - prompt(s)
   - visible report title
   - key visible columns
   - pass/fail
   - screenshot if failed
5. A case fails if any of these happen:
   - wrong report
   - wrong grain
   - stale topic carryover
   - wrong transform or projection behavior
   - repeated prompt needed to succeed
   - debug/internal leakage

## 3. Evidence Recording Format

For each pack, record:

1. Session ID or session label
2. Prompt sequence
3. Observed result title
4. Observed shape
5. Pass/fail
6. Notes

## 4. Pack A: Customer Ranking + Scale

Risk tier: `Tier 1`

Fresh chat required: `Yes`

Prompts:

1. `Top 10 customers by revenue last month`
2. `Show as Million`
3. `Show as Million`

Expected:

1. report stays `Customer Ledger Summary`
2. same ranked customer set is preserved
3. first scale follow-up converts values to millions
4. second scale follow-up remains stable and does not drift or collapse

Pass rule:

all three turns preserve the same result authority and ranking context

## 5. Pack B: Product Ranking + Projection

Risk tier: `Tier 2`

Fresh chat required: `Yes`

Prompts:

1. `Top 10 products by sold quantity last month`
2. `with Item Name`
3. `Give me Item Name and Sold Qty only`
4. `Give me Item Name Only`

Expected:

1. first turn returns product ranking by sold quantity
2. second turn adds `Item Name`
3. third turn keeps only `Item Name` and sold quantity columns
4. fourth turn keeps only `Item Name`

Pass rule:

projection follow-ups stay on the same active result and do not drift to another report

## 6. Pack C: Supplier Ranking + Scale

Risk tier: `Tier 1`

Fresh chat required: `Yes`

Prompts:

1. `Top 10 suppliers by purchase amount last month`
2. `Show in Million`

Expected:

1. report stays `Supplier Ledger Summary`
2. purchase amount remains the metric
3. same supplier set is preserved
4. values are scaled to millions

## 7. Pack D: Warehouse Ranking Correction + Scale

Risk tier: `Tier 1`

Fresh chat required: `Yes`

Prompts:

1. `Lowest 3 warehouses by stock balance`
2. `I mean Top`
3. `Show as Million`

Expected:

1. first turn shows bottom 3 warehouses
2. correction rebind switches to top warehouses
3. scale follow-up preserves the corrected warehouse set and metric

## 8. Pack E: Latest-Record Clarification

Risk tier: `Tier 1`

Fresh chat required: `Yes`

Prompts:

1. `Show me the latest 7 Invoice`
2. `Sales Invoice`

Expected:

1. first turn asks which record type
2. second turn returns latest 7 Sales Invoices
3. no extra clarification loop occurs

## 9. Pack F: Finance Parity

Risk tier: `Tier 1`

Fresh chat required: `Yes`

Prompts:

1. `Show accounts receivable as of today`
2. New fresh chat: `Show me the latest Purchase 7 Invoice`

Expected:

1. first prompt returns finance/receivables result on the correct report path
2. second prompt returns latest purchase invoices on the latest-record path

## 10. Pack G: Write Confirm/Cancel Safety

Risk tier: `Tier 1`

Fresh chat required: `Yes`

Prompts:

1. `Delete ToDo TEST-123`
2. `cancel`

Expected:

1. first turn asks for explicit confirmation or returns the approved write-safety block for the current environment
2. second turn cancels safely or remains safely blocked without executing any write

Operational note:

For the current environment, safe-block behavior is acceptable if write actions are globally disabled.

## 11. Optional Comparison Closure Spot-Check

This is not part of the original standing pack, but it is useful as a post-Phase-3 confidence spot-check.

Fresh chat required: `Yes`

Prompts:

1. `Compare Yangon and Mandalay sales last month by territory`
2. `Show in Million`

Expected:

1. `Sales Analytics`
2. side-by-side comparison shape is preserved
3. scale follow-up preserves side-by-side comparison shape

## 12. Minimum Outcome Rule

This refresh is considered successful only when:

1. every mandatory pack above is executed
2. every Tier 1 pack passes
3. any Tier 2 failure is recorded explicitly and assessed for severity
4. no browser/replay contradiction is ignored

## 13. What To Do With Results

After execution:

1. update the weekly operations review baseline with fresh browser results
2. open incidents for any P1/P2 failures
3. do not fix anything informally before the failure is classified

## 14. Immediate Next Step

Run this pack once, paste the results, and then convert the weekly baseline from carry-forward browser status to fresh Phase 4 operational status.
