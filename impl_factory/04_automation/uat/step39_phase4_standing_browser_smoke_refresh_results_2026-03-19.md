# Phase 4 Standing Browser Smoke Refresh Results

Date: 2026-03-19  
Owner: AI Runtime Engineering  
Scope: first executed Phase 4 standing browser smoke refresh, plus same-day Pack B incident rerun  
Status: completed, all standing packs green after bounded incident remediation

## 1. Outcome Summary

The first Phase 4 standing browser smoke refresh was executed, and the one failing pack was rerun after a bounded shaper-layer fix.

Result summary:

1. all Tier 1 packs passed
2. the initial Tier 2 Pack B failure was reproduced, fixed, and rerun successfully
3. optional comparison spot-check passed

Operational meaning:

1. no Tier 1 blocker was found in this refresh
2. the one user-visible Tier 2 projection drift was resolved the same day under the Phase 4 incident process
3. the standing browser pack is now green on fresh evidence

## 2. Pack Results

### Pack A: Customer Ranking + Scale

Status: `PASS`

Observed:

1. `Top 10 customers by revenue last month`
   - report: `Customer Ledger Summary`
   - columns: `Customer`, `Revenue`
2. first `Show as Million`
   - report stayed `Customer Ledger Summary`
   - same customer set preserved
   - values scaled to millions
3. second `Show as Million`
   - report stayed `Customer Ledger Summary`
   - same customer set preserved
   - values remained stable

Assessment:

1. ranking authority preserved
2. repeated scale follow-up idempotent on this pack

### Pack B: Product Ranking + Projection

Status: `PASS after incident rerun`

Observed:

1. `Top 10 products by sold quantity last month`
   - report: `Item-wise Sales Register`
   - columns: `Item`, `Sold Quantity`
2. `with Item Name`
   - report stayed `Item-wise Sales Register`
   - columns: `Item`, `Sold Quantity`, `Item Name`
   - status: good
3. `Give me Item Name and Sold Qty only`
   - report stayed `Item-wise Sales Register`
   - columns: `Item Name`, `Sold Quantity`
   - visible behavior drift:
     - duplicate item names were merged
     - `Type-C Cable 1m Fast Charge` became `614.00` instead of preserving original active-result row authority
4. `Give me Item Name Only`
   - report stayed `Item-wise Sales Register`
   - item-name-only projection produced the drifted deduplicated set, not a strict projection of the active ranked rows

Initial assessment:

1. this was not just column restriction
2. it changed row authority by grouping or aggregation
3. this was a user-visible projection/shaping defect on a supported standing-pack flow

Incident handling and rerun:

1. Phase 4 incident `INC-P4-001` was opened
2. root cause was confirmed in the top-N shaper path
3. a bounded fix was applied so projection-only top-N follow-ups preserve row authority instead of regrouping duplicate visible values
4. fresh browser rerun result:
   - `Give me Item Name and Sold Qty only`
   - rows stayed separate
   - `Type-C Cable 1m Fast Charge` remained `412.00` and `222.00`, not `614.00`
5. `Give me Item Name Only` also preserved row authority by keeping duplicate names from separate ranked rows

Final assessment:

1. Pack B is now green
2. active-result projection contract is preserved
3. the incident can be treated as resolved/closed

### Pack C: Supplier Ranking + Scale

Status: `PASS`

Observed:

1. `Top 10 suppliers by purchase amount last month`
   - report: `Supplier Ledger Summary`
   - columns: `Supplier`, `Purchase Amount`
2. `Show in Million`
   - report stayed `Supplier Ledger Summary`
   - same supplier set preserved
   - values scaled correctly

### Pack D: Warehouse Ranking Correction + Scale

Status: `PASS`

Observed:

1. `Lowest 3 warehouses by stock balance`
   - report: `Warehouse Wise Stock Balance`
   - columns: `Warehouse`, `Stock Balance`
2. `I mean Top`
   - report stayed `Warehouse Wise Stock Balance`
   - corrected warehouse set returned
3. `Show as Million`
   - corrected warehouse set preserved
   - values scaled correctly

### Pack E: Latest-Record Clarification

Status: `PASS`

Observed:

1. `Show me the latest 7 Invoice`
   - clarification question asked correctly
2. `Sales Invoice`
   - report: `Latest Sales Invoice`
   - latest sales invoices returned

Additional note:

1. follow-up detail request on a returned invoice also worked in the tested session
2. this additional note is informative and not required for pack pass

### Pack F: Finance Parity

Status: `PASS`

Observed:

1. `Show accounts receivable as of today`
   - report: `Customer Ledger Summary`
   - visible shape: `Metric`, `Value`
   - finance path selected correctly
2. `Show me the latest Purchase 7 Invoice`
   - report: `Latest Purchase Invoice`
   - latest purchase invoice path selected correctly

Assessment:

finance parity is correct for the tested standing prompts

### Pack G: Write Confirm/Cancel Safety

Status: `PASS`

Observed:

1. `Delete ToDo TEST-123`
   - assistant asked for explicit confirmation
2. `cancel`
   - assistant returned `Write action canceled.`

Assessment:

write cancel safety works correctly in the browser path

### Optional Comparison Spot-Check

Status: `PASS`

Observed:

1. `Compare Yangon and Mandalay sales last month by territory`
   - report: `Sales Analytics`
   - side-by-side comparison shape correct
2. `Show in Million`
   - side-by-side comparison shape preserved
   - scale follow-up correct

## 3. Overall Assessment

This refresh is operationally successful because:

1. all Tier 1 packs passed
2. the one Tier 2 failure was captured explicitly, fixed, and rerun
3. no browser/replay contradiction was ignored

The refresh is now fully green at the standing-pack level.

## 4. Required Follow-Up

1. update the weekly operations review baseline with the Pack B rerun outcome
2. close `INC-P4-001` with linked fix and regression evidence
3. keep replay/manual parity discipline unchanged for future Phase 4 incidents
